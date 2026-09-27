"""Tests for the estimated-cost feature (engine/recommender.py's
_estimate_packaging_cost_per_unit / _build_cost_comparison_note, and their
wiring into recommend_detailed's estimated_cost_per_unit_inr /
cost_comparison_note fields).

Purely additive/informational — these tests specifically also confirm the
existing ranking/budget_tier behavior is completely unaffected, since that
was an explicit constraint on this feature.
"""

from engine.recommender import (
    _build_cost_comparison_note,
    _estimate_packaging_cost_per_unit,
    _materials,
    _rules,
    find_commodity,
    recommend,
    recommend_detailed,
)

# Spans old and new categories added in the 80-commodity expansion.
SAMPLE_COMMODITY_IDS = [
    "banana",  # fresh_fruit
    "cheddar_cheese",  # dairy
    "rice",  # dry_goods_grains
    "turmeric_powder",  # spices
    "chicken_fresh",  # meat_fish
    "white_bread",  # bakery
    "almonds",  # nuts_dried_fruits (new category)
    "fruit_juice_bottled",  # beverages (new category)
]


# ---------------------------------------------------------------------------
# Cost fields appear correctly across commodities/categories
# ---------------------------------------------------------------------------


def test_estimated_cost_present_and_sane_across_categories():
    for commodity_id in SAMPLE_COMMODITY_IDS:
        result = recommend_detailed(commodity_id)
        assert result is not None, commodity_id
        for rec in result["recommendations"]:
            cost = rec["estimated_cost_per_unit_inr"]
            assert cost is not None, f"{commodity_id}/{rec['material_id']} missing cost"
            assert cost["min"] > 0
            assert cost["max"] >= cost["min"]
            assert rec["cost_comparison_note"] is not None


def test_top_pick_cost_comparison_note_is_reference_phrase():
    result = recommend_detailed("banana")
    top = result["recommendations"][0]
    assert top["cost_comparison_note"] == "Reference point for the cost comparisons below."


def test_estimate_packaging_cost_per_unit_returns_none_without_cost_data():
    rules = _rules()
    commodity = find_commodity("banana")
    material_missing_cost = {**_materials()[0]}
    del material_missing_cost["estimated_cost_per_kg_inr"]
    assert _estimate_packaging_cost_per_unit(commodity, material_missing_cost, rules) is None


def test_estimate_packaging_cost_per_unit_returns_none_without_weight_multiplier():
    rules = _rules()
    commodity = find_commodity("banana")
    material_missing_multiplier = {**_materials()[0]}
    del material_missing_multiplier["material_weight_multiplier"]
    assert _estimate_packaging_cost_per_unit(commodity, material_missing_multiplier, rules) is None


def test_estimate_packaging_cost_per_unit_uses_category_default_for_unknown_category():
    rules = _rules()
    material = _materials()[0]
    fake_commodity = {"category": "not_a_real_category"}
    result = _estimate_packaging_cost_per_unit(fake_commodity, material, rules)
    default_weight = rules["packaging_weight_g_per_kg_product_by_category"]["default"]
    cost_per_kg = material["estimated_cost_per_kg_inr"]
    weight_multiplier = material["material_weight_multiplier"]
    assert result == {
        "min": round(cost_per_kg["min"] * (default_weight["min"] / 1000) * weight_multiplier["min"], 2),
        "max": round(cost_per_kg["max"] * (default_weight["max"] / 1000) * weight_multiplier["max"], 2),
    }


# ---------------------------------------------------------------------------
# The specific fix: glass no longer implausibly undercuts flexible films
# ---------------------------------------------------------------------------


def test_glass_is_no_longer_implausibly_cheaper_than_flexible_film():
    """Before material_weight_multiplier existed, glass's low per-kg material price
    (raw glass is cheap) combined with a category-only packaging-weight estimate made
    it look several times cheaper than a comparable flexible film — physically
    implausible, since glass containers use far more material mass per kg of product.
    This doesn't assert glass must be MORE expensive than film (real packaging
    economics are more nuanced than this estimate captures — see
    packaging_format_practicality for the separate weight/fragility cost dimension),
    only that the gap is no longer an order-of-magnitude distortion: their estimated
    cost ranges should now meaningfully overlap for a representative sample of
    commodities."""
    rules = _rules()
    materials = {m["id"]: m for m in _materials()}
    glass = materials["glass"]
    ldpe = materials["ldpe"]

    for commodity_id in ["rice", "turmeric_powder", "cheddar_cheese"]:
        commodity = find_commodity(commodity_id)
        glass_cost = _estimate_packaging_cost_per_unit(commodity, glass, rules)
        ldpe_cost = _estimate_packaging_cost_per_unit(commodity, ldpe, rules)

        glass_mid = (glass_cost["min"] + glass_cost["max"]) / 2
        ldpe_mid = (ldpe_cost["min"] + ldpe_cost["max"]) / 2

        # Old (pre-fix) behavior put glass roughly 4-5x cheaper than a flexible film for
        # a commodity like rice — assert that gap is now well under 2x, not eliminated
        # outright (glass's raw material genuinely is cheaper per kg; the fix corrects
        # the mass-per-package blind spot, it doesn't force glass to be pricier).
        ratio = ldpe_mid / glass_mid
        assert ratio < 2.0, f"{commodity_id}: glass ({glass_mid}) still implausibly cheaper than LDPE ({ldpe_mid})"


# ---------------------------------------------------------------------------
# Percentage delta calculation correctness
# ---------------------------------------------------------------------------


def test_cost_comparison_note_percentage_more_expensive():
    top_pick_cost = {"min": 8, "max": 12}  # mid = 10
    candidate_cost = {"min": 11, "max": 15}  # mid = 13 -> +30%
    note = _build_cost_comparison_note(candidate_cost, top_pick_cost, is_top_pick=False)
    assert note == "Approximately 30% more expensive than the top pick (estimated)."


def test_cost_comparison_note_percentage_less_expensive():
    top_pick_cost = {"min": 18, "max": 22}  # mid = 20
    candidate_cost = {"min": 9, "max": 11}  # mid = 10 -> -50%
    note = _build_cost_comparison_note(candidate_cost, top_pick_cost, is_top_pick=False)
    assert note == "Approximately 50% less expensive than the top pick (estimated)."


def test_cost_comparison_note_comparable_within_5_percent():
    top_pick_cost = {"min": 19, "max": 21}  # mid = 20
    candidate_cost = {"min": 20, "max": 21}  # mid = 20.5 -> +2.5%, under the 5% threshold
    note = _build_cost_comparison_note(candidate_cost, top_pick_cost, is_top_pick=False)
    assert note == "Comparable estimated cost to the top pick."


def test_cost_comparison_note_none_when_cost_data_missing():
    assert _build_cost_comparison_note(None, {"min": 1, "max": 2}, is_top_pick=False) is None
    assert _build_cost_comparison_note({"min": 1, "max": 2}, None, is_top_pick=False) is None


# ---------------------------------------------------------------------------
# Existing behavior (ranking, budget_tier influence, plain recommend()) unaffected
# ---------------------------------------------------------------------------


def test_plain_recommend_has_no_cost_fields():
    result = recommend("banana")
    for rec in result["recommendations"]:
        assert "estimated_cost_per_unit_inr" not in rec
        assert "cost_comparison_note" not in rec


def test_ranking_order_unaffected_by_cost_fields():
    """Ranking must still be driven purely by the rules-engine score, unaffected
    by adding cost fields — same score ordering as before this feature existed."""
    result = recommend_detailed("strawberry")
    scores = [r["score"] for r in result["recommendations"]]
    assert scores == sorted(scores, reverse=True)


def test_budget_tier_still_influences_scoring_directionally():
    """budget_tier's existing directional ranking influence must be completely
    unchanged by this feature — economy should still score cost more heavily
    than premium for at least one non-top material."""
    from engine.recommender import _score_material

    rules = _rules()
    commodity = find_commodity("cheddar_cheese")
    materials = {m["id"]: m for m in _materials()}
    cheap_material = materials["pp"]  # low cost_tier

    economy_score = _score_material(
        commodity, cheap_material, rules, {"budget_tier": "low", "prioritize_sustainability": False}
    )["score"]
    premium_score = _score_material(
        commodity, cheap_material, rules, {"budget_tier": "high", "prioritize_sustainability": False}
    )["score"]
    # A cheap material should score relatively better under a low (economy) budget
    # tier than under a high (premium) one — same directional check as before this
    # feature was added, confirming cost-fit's weight multiplier is untouched.
    assert economy_score > premium_score
