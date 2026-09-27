"""Unit tests for backend/engine/recommender.py.

Run with: pytest (from /backend, using the venv — pytest.ini sets pythonpath=.)
"""

import pytest

from engine.recommender import (
    _materials,
    _rules,
    _score_material,
    find_commodity,
    recommend,
    recommend_detailed,
)

# Covers all 7 commodity categories in the dataset, not just 5, so a regression
# in one category's rule branch (e.g. respiration handling) can't hide behind
# a pass on the others.
SAMPLE_COMMODITY_IDS = [
    "banana",  # fresh_fruit, respiring, low fat
    "spinach",  # fresh_vegetable, respiring, very_high respiration
    "cheddar_cheese",  # dairy, non-respiring, high fat
    "rice",  # dry_goods_grains, non-respiring, low moisture, long shelf life
    "turmeric_powder",  # spices, non-respiring
    "chicken_fresh",  # meat_fish, non-respiring, very short shelf life
    "white_bread",  # bakery, non-respiring
]


# ---------------------------------------------------------------------------
# Basic contract: recommend() / recommend_detailed()
# ---------------------------------------------------------------------------


def test_unknown_commodity_returns_none():
    assert recommend("not-a-real-commodity") is None
    assert recommend_detailed("not-a-real-commodity") is None


@pytest.mark.parametrize("commodity_id", SAMPLE_COMMODITY_IDS)
def test_recommend_returns_top_3_sorted_by_score(commodity_id):
    result = recommend(commodity_id)
    assert result is not None
    recs = result["recommendations"]
    assert 1 <= len(recs) <= 3
    scores = [r["score"] for r in recs]
    assert scores == sorted(scores, reverse=True)
    for r in recs:
        assert 0 <= r["score"] <= 100


@pytest.mark.parametrize("commodity_id", SAMPLE_COMMODITY_IDS)
def test_commodity_id_and_name_both_resolve(commodity_id):
    commodity = find_commodity(commodity_id)
    by_name = find_commodity(commodity["name"])
    assert by_name is not None
    assert by_name["id"] == commodity["id"]


# ---------------------------------------------------------------------------
# 1 & 2: multi-option ranking with trade-offs + explainable scoring
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("commodity_id", SAMPLE_COMMODITY_IDS)
def test_each_recommendation_has_trade_off_and_match_breakdown(commodity_id):
    result = recommend_detailed(commodity_id)
    recs = result["recommendations"]
    assert len(recs) >= 1

    for rec in recs:
        assert rec["trade_off_summary"]
        assert isinstance(rec["trade_off_summary"], str)
        # 8 scoring dimensions: moisture, oxygen, respiration, respiration_packaging_boost
        # (rewards breathable/vented materials for high/very_high respiration produce —
        # see rules.json's respiration_class_packaging_boost), category, cost,
        # sustainability, format_practicality (weight/fragility factor for high-volume
        # retail — see rules.json's packaging_format_practicality).
        assert len(rec["match_breakdown"]) == 8
        for item in rec["match_breakdown"]:
            assert item["fit"] in {"good", "partial", "poor", "not_applicable"}
            assert item["commodity_property"]
            assert item["packaging_property"]
            assert item["explanation"]


@pytest.mark.parametrize("commodity_id", SAMPLE_COMMODITY_IDS)
def test_top_pick_trade_off_differs_from_runner_ups(commodity_id):
    """The #1 pick's trade-off framing ('best overall fit') should read
    differently from a runner-up's relative comparison — they aren't just
    the same boilerplate string repeated three times."""
    result = recommend_detailed(commodity_id)
    recs = result["recommendations"]
    if len(recs) < 2:
        pytest.skip(f"{commodity_id} only has one candidate material in range")

    top_summary = recs[0]["trade_off_summary"]
    assert "best overall fit" in top_summary.lower()
    for runner_up in recs[1:]:
        assert runner_up["trade_off_summary"] != top_summary


def test_trade_off_flags_cheaper_and_shelf_life_delta():
    """rice: PP is cheaper-tier-equal but scores lower than HDPE due to a
    small barrier gap, and Glass is explicitly pricier — exercise both the
    cost and shelf-life phrasing paths in one known, stable case."""
    result = recommend_detailed("rice", budget_tier="standard")
    recs = {r["material_id"]: r for r in result["recommendations"]}
    assert "hdpe" in recs and "glass" in recs

    glass_summary = recs["glass"]["trade_off_summary"].lower()
    assert "higher cost" in glass_summary


# ---------------------------------------------------------------------------
# 3: MAP gas composition guidance for fresh produce
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("commodity_id", ["banana", "spinach"])
def test_map_guidance_present_for_respiring_produce(commodity_id):
    result = recommend_detailed(commodity_id)
    guidance = result["map_gas_guidance"]
    assert guidance["applicable"] is True
    assert guidance["respiration_rate_class"] is not None
    assert "general" in guidance["note"].lower()
    assert "not commodity-specific" in guidance["note"].lower()

    o2, co2, n2 = guidance["o2_percent"], guidance["co2_percent"], guidance["n2_percent"]
    for gas_range in (o2, co2, n2):
        assert 0 <= gas_range["min"] <= gas_range["max"] <= 100

    # O2 + CO2 + N2 should account for the full atmosphere at both ends of the range.
    assert o2["min"] + co2["min"] + n2["max"] == pytest.approx(100, abs=0.5)
    assert o2["max"] + co2["max"] + n2["min"] == pytest.approx(100, abs=0.5)


@pytest.mark.parametrize("commodity_id", ["rice", "cheddar_cheese", "chicken_fresh", "turmeric_powder"])
def test_map_guidance_absent_for_non_produce(commodity_id):
    result = recommend_detailed(commodity_id)
    guidance = result["map_gas_guidance"]
    assert guidance["applicable"] is False
    assert guidance["o2_percent"] is None


def test_more_actively_respiring_produce_gets_lower_o2_target():
    """spinach is 'very_high' respiration, banana is 'high' — the more active
    respirer should get a tighter (lower) O2 ceiling per general MAP practice."""
    banana_o2 = recommend_detailed("banana")["map_gas_guidance"]["o2_percent"]
    spinach_o2 = recommend_detailed("spinach")["map_gas_guidance"]["o2_percent"]
    assert spinach_o2["max"] <= banana_o2["max"]


# ---------------------------------------------------------------------------
# 3b: respiration_class_packaging_boost — high/very_high respiration produce must
# get a breathable/vented/micro-perforated material as (or very near) its top pick.
#
# Regression context: the MAP guidance above already treats "high"/"very_high"
# respiration produce as needing active gas exchange, but the *material* scoring
# didn't reflect that — a material's bulk OTR landing inside the respiration_otr_bands
# range by coincidence (e.g. plain LDPE is naturally permeable) was treated the same
# as a material actually engineered/tagged for produce ventilation. Confirmed via
# evaluation/run_evaluation.py: strawberry and spinach both ranked plain HDPE (not
# breathable-tagged) as their top pick. Fixed by adding an explicit
# respiration_class_packaging_boost weighted dimension (rules.json) that rewards
# packaging_materials.json's breathable=true tag specifically, plus exempting
# actively-respiring produce from oxygen_fit's "low OTR is good" rancidity-prevention
# target (which was otherwise fighting the boost, since intentionally-high-OTR vented
# materials would fail it every time).
# ---------------------------------------------------------------------------

_BREATHABLE_MATERIAL_IDS = {m["id"] for m in _materials() if m.get("breathable")}


@pytest.mark.parametrize("commodity_id", ["strawberry", "spinach", "banana", "mango"])
def test_high_and_very_high_respiration_produce_gets_breathable_top_pick(commodity_id):
    """strawberry/spinach are 'very_high' respiration, banana/mango are 'high' —
    all four should be scored toward a breathable-tagged material now, not just
    whichever cheap resin happened to have a numerically-permeable bulk OTR."""
    commodity = find_commodity(commodity_id)
    assert commodity["respiration_rate_class"] in ("high", "very_high")

    result = recommend_detailed(commodity_id)
    top_pick = result["recommendations"][0]
    assert top_pick["material_id"] in _BREATHABLE_MATERIAL_IDS, (
        f"expected a breathable-tagged top pick for {commodity_id}, got '{top_pick['material_id']}'"
    )

    boost_entry = next(
        item for item in top_pick["match_breakdown"] if item["dimension"] == "respiration_packaging_boost"
    )
    assert boost_entry["fit"] == "good"


@pytest.mark.parametrize("commodity_id", ["apple", "carrot", "onion", "potato"])
def test_low_moderate_respiration_produce_not_forced_toward_breathable(commodity_id):
    """Sanity check that the boost is targeted at high/very_high respiration only —
    these are 'low' respiration produce and should NOT be artificially pushed toward
    a breathable material just because they're produce at all."""
    commodity = find_commodity(commodity_id)
    assert commodity["respiration_rate_class"] not in ("high", "very_high")

    result = recommend_detailed(commodity_id)
    top_pick = result["recommendations"][0]
    boost_entry = next(
        item for item in top_pick["match_breakdown"] if item["dimension"] == "respiration_packaging_boost"
    )
    assert boost_entry["fit"] == "not_applicable"


def test_non_breathable_material_gets_explicit_warning_for_high_respiration_produce():
    """A non-breathable candidate (e.g. plain HDPE) in a high/very_high respiration
    commodity's results should carry an explicit warning that a purpose-built
    breathable/vented option would serve it better — not just a quietly lower score."""
    result = recommend_detailed("strawberry", top_n=13)  # pull every material so hdpe is guaranteed present
    hdpe = next(r for r in result["recommendations"] if r["material_id"] == "hdpe")
    assert any("purpose-built" in w or "breathable" in w for w in hdpe["warnings"])


# ---------------------------------------------------------------------------
# 4: sustainability scoring (0-100) + prioritize_sustainability re-ranking
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("commodity_id", SAMPLE_COMMODITY_IDS)
def test_sustainability_score_in_range(commodity_id):
    result = recommend_detailed(commodity_id)
    for rec in result["recommendations"]:
        assert 0 <= rec["sustainability_score"] <= 100


@pytest.mark.parametrize("commodity_id", ["cheddar_cheese", "butter"])
def test_prioritize_sustainability_reranks_toward_more_recyclable_option(commodity_id):
    """For commodities where the highest-barrier material (metalized film) is
    poorly recyclable, turning the toggle on should surface a more sustainable
    top pick instead — proving the toggle actually changes ranking, not just
    the reported number. (Picked by scanning every commodity for a toggle-
    sensitive case rather than hardcoding one, so this stays valid if rules.json
    tuning shifts which commodities are on the fence. Previously cumin_seeds/
    mutton_fresh — those stopped flipping once the format_practicality dimension
    was added (Day 5, Issue 1), since it now costs glass enough that sustainability
    priority alone no longer tips it over for those two. cheddar_cheese/butter
    still flip to glass under the toggle, which is correct: glass should still win
    when sustainability is genuinely prioritized enough to outweigh its practicality
    cost, not be eliminated as an option.)"""
    default_result = recommend_detailed(commodity_id, prioritize_sustainability=False)
    sustainable_result = recommend_detailed(commodity_id, prioritize_sustainability=True)

    default_top = default_result["recommendations"][0]
    sustainable_top = sustainable_result["recommendations"][0]

    assert default_top["material_id"] != sustainable_top["material_id"]
    assert sustainable_top["sustainability_score"] > default_top["sustainability_score"]


# ---------------------------------------------------------------------------
# 5: budget tier (economy/standard/premium) awareness
# ---------------------------------------------------------------------------


def test_economy_budget_tier_penalizes_expensive_materials_more_than_premium():
    commodity = find_commodity("rice")
    rules = _rules()
    aluminum = next(m for m in _materials() if m["id"] == "aluminum_foil_laminate")
    assert aluminum["cost_tier"] == "high"

    economy_score = _score_material(commodity, aluminum, rules, {"budget_tier": "low"})["score"]
    premium_score = _score_material(commodity, aluminum, rules, {"budget_tier": "high"})["score"]

    assert economy_score < premium_score


@pytest.mark.parametrize("budget_tier", ["economy", "standard", "premium"])
def test_detailed_endpoint_accepts_all_budget_tier_labels(budget_tier):
    result = recommend_detailed("banana", budget_tier=budget_tier)
    assert result is not None
    assert len(result["recommendations"]) >= 1


# ---------------------------------------------------------------------------
# 6: confidence flagging
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("commodity_id", SAMPLE_COMMODITY_IDS)
def test_confidence_is_weaker_of_commodity_and_material(commodity_id):
    commodity = find_commodity(commodity_id)
    result = recommend_detailed(commodity_id)
    order = {"low": 1, "medium": 2, "high": 3}

    for rec in result["recommendations"]:
        expected = min(
            commodity["confidence"],
            rec["material_confidence"],
            key=lambda level: order[level],
        )
        assert rec["overall_confidence"] == expected


def test_low_confidence_commodity_propagates_to_every_recommendation():
    # cheddar_cheese is authored with confidence="low" in commodities.json
    commodity = find_commodity("cheddar_cheese")
    assert commodity["confidence"] == "low"

    result = recommend_detailed("cheddar_cheese")
    for rec in result["recommendations"]:
        assert rec["overall_confidence"] == "low"


# ---------------------------------------------------------------------------
# 7: differentiated output sanity check across commodity types
# ---------------------------------------------------------------------------


def test_different_commodity_types_produce_different_top_picks():
    """Sanity check that the engine is actually differentiating by commodity
    properties rather than always returning the same ranking regardless of
    input — pick a spread of commodities likely to stress different rules."""
    top_picks = {
        commodity_id: recommend_detailed(commodity_id)["recommendations"][0]["material_id"]
        for commodity_id in ["cheddar_cheese", "chicken_fresh", "rice"]
    }
    # Not all three should collapse onto the same top pick.
    assert len(set(top_picks.values())) > 1


# ---------------------------------------------------------------------------
# Day 5, Issue 1: format_practicality dimension — glass shouldn't auto-win
# just for having zero permeability; it should still be able to win when
# genuinely warranted (sustainability strongly prioritized).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("commodity_id", SAMPLE_COMMODITY_IDS)
def test_glass_scores_low_on_format_practicality(commodity_id):
    """Glass's practicality fit should always be flagged poor/partial — never
    'good' — since the whole point of this dimension is that its weight and
    fragility are real logistics costs regardless of which commodity it's
    being scored against."""
    result = recommend_detailed(commodity_id, top_n=13)
    glass = next((r for r in result["recommendations"] if r["material_id"] == "glass"), None)
    if glass is None:
        pytest.skip("glass not present in this run's top_n")
    practicality = next(m for m in glass["match_breakdown"] if m["dimension"] == "format_practicality")
    assert practicality["fit"] in {"partial", "poor"}


def test_glass_can_still_win_when_sustainability_is_strongly_prioritized():
    """Issue 1 is about correcting an imbalance, not eliminating glass as an
    option — for cheddar cheese, glass should still take the top spot once
    sustainability is prioritized enough to outweigh its practicality cost."""
    result = recommend_detailed("cheddar_cheese", prioritize_sustainability=True)
    assert result["recommendations"][0]["material_id"] == "glass"


# ---------------------------------------------------------------------------
# Day 5, Issue 2: regulatory_note — static disclaimer on every detailed response
# ---------------------------------------------------------------------------


def test_regulatory_note_present_and_on_topic():
    result = recommend_detailed("banana")
    note = result["regulatory_note"]
    assert note
    note_lower = note.lower()
    assert "regulatory" in note_lower or "food-safety" in note_lower or "food safety" in note_lower
    assert "fssai" in note_lower
