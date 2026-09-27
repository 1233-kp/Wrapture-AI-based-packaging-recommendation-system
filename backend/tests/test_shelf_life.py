"""Tests for the Q10 temperature-adjusted shelf-life prediction
(engine/shelf_life.py and its wiring into recommend_detailed's
shelf_life_prediction field).

Purely informational and material-independent — these tests also confirm
plain recommend() is untouched and ranking/scoring is unaffected.
"""

from fastapi.testclient import TestClient

from engine.recommender import find_commodity, recommend, recommend_detailed
from engine.shelf_life import predict_shelf_life
from main import app

client = TestClient(app)


def _has_devanagari(text: str) -> bool:
    return any("ऀ" <= ch <= "ॿ" for ch in text)


def _typical_midpoint(commodity_id: str) -> float:
    c = find_commodity(commodity_id)
    r = c["typical_ambient_shelf_life_days"]
    return (r["min"] + r["max"]) / 2


# ---------------------------------------------------------------------------
# Core Q10 math
# ---------------------------------------------------------------------------


def test_temp_equal_to_reference_gives_exact_typical_shelf_life():
    banana = find_commodity("banana")  # fresh_fruit, reference_temperature_c = 25
    result = predict_shelf_life(banana, 25)
    assert result is not None
    assert result["predicted_shelf_life_days"] == round(_typical_midpoint("banana"), 1)
    assert result["was_clamped"] is False


def test_higher_temp_gives_shorter_predicted_life():
    banana = find_commodity("banana")
    at_reference = predict_shelf_life(banana, 25)["predicted_shelf_life_days"]
    at_warmer = predict_shelf_life(banana, 36)["predicted_shelf_life_days"]
    assert at_warmer < at_reference


def test_lower_temp_gives_longer_predicted_life():
    banana = find_commodity("banana")
    at_reference = predict_shelf_life(banana, 25)["predicted_shelf_life_days"]
    at_cooler = predict_shelf_life(banana, 15)["predicted_shelf_life_days"]
    assert at_cooler > at_reference


def test_monotonic_across_a_temperature_range():
    """Predicted shelf life should strictly decrease as temperature rises,
    across the whole range our form actually offers (4/15/25/36C presets)."""
    banana = find_commodity("banana")
    values = [predict_shelf_life(banana, t)["predicted_shelf_life_days"] for t in [4, 15, 25, 36]]
    assert values == sorted(values, reverse=True)


# ---------------------------------------------------------------------------
# Clamping
# ---------------------------------------------------------------------------


def test_clamping_triggers_at_extreme_cold_and_floors_correctly():
    banana = find_commodity("banana")
    result = predict_shelf_life(banana, -40)
    typical = _typical_midpoint("banana")
    assert result["was_clamped"] is True
    assert result["predicted_shelf_life_days"] <= round(typical * 3.0, 1)


def test_clamping_triggers_at_a_realistic_refrigerated_temperature_for_a_fast_q10_category():
    """4C (our 'Refrigerated' preset) is a normal, realistic input — but for a
    fast-spoiling category like fresh_fruit (Q10=2.2) with a 25C ambient
    reference, the 21C gap alone implies ~5x longer shelf life, above the 3x
    cap. Documents that this is a real, expected clamp case, not just an
    extreme-input edge case."""
    banana = find_commodity("banana")
    result = predict_shelf_life(banana, 4)
    assert result["was_clamped"] is True
    typical = _typical_midpoint("banana")
    assert result["predicted_shelf_life_days"] == round(typical * 3.0, 1)


def test_clamping_triggers_at_extreme_heat_and_floors_at_min_days():
    banana = find_commodity("banana")
    result = predict_shelf_life(banana, 80)
    assert result["was_clamped"] is True
    assert result["predicted_shelf_life_days"] >= 0.5


def test_no_clamping_near_the_reference_temperature():
    """4C is a real preset in our form but genuinely DOES clamp for banana
    (Q10=2.2, a 21C gap from the 25C reference implies ~26.8 raw days against
    a 15.0-day cap) — that's correct, expected clamp behavior, not a bug, so
    it's covered by the clamping tests instead. This test only checks
    temperatures close enough to the reference that no clamp is expected."""
    banana = find_commodity("banana")
    for temp in [20, 25, 30]:
        result = predict_shelf_life(banana, temp)
        assert result["was_clamped"] is False, temp


# ---------------------------------------------------------------------------
# Missing input -> field omitted, not fabricated
# ---------------------------------------------------------------------------


def test_no_temperature_supplied_returns_none():
    banana = find_commodity("banana")
    assert predict_shelf_life(banana, None) is None


def test_recommend_detailed_omits_field_when_no_temperature_given():
    result = recommend_detailed("banana")
    assert result["shelf_life_prediction"] is None


def test_recommend_detailed_includes_field_when_temperature_given():
    result = recommend_detailed("banana", ambient_temperature_c=30)
    assert result["shelf_life_prediction"] is not None
    prediction = result["shelf_life_prediction"]
    assert set(prediction.keys()) == {
        "predicted_shelf_life_days",
        "shelf_life_confidence",
        "explanation",
        "was_clamped",
        "disclaimer",
    }


def test_unknown_category_or_missing_baseline_returns_none():
    fake_commodity = {"category": "not_a_real_category", "typical_ambient_shelf_life_days": {"min": 1, "max": 2}}
    assert predict_shelf_life(fake_commodity, 25) is None

    fake_commodity_2 = {"category": "fresh_fruit", "typical_ambient_shelf_life_days": None}
    assert predict_shelf_life(fake_commodity_2, 25) is None


# ---------------------------------------------------------------------------
# Category coverage: every category in commodities.json has Q10 config
# ---------------------------------------------------------------------------


def test_every_commodity_category_has_a_shelf_life_prediction():
    from engine.recommender import list_commodities

    missing = []
    for commodity in list_commodities():
        if commodity.get("typical_ambient_shelf_life_days") is None:
            continue
        if predict_shelf_life(commodity, 25) is None:
            missing.append(commodity["id"])
    assert not missing, f"No Q10 config for categories of: {missing}"


# ---------------------------------------------------------------------------
# English/Hindi explanation text
# ---------------------------------------------------------------------------


def test_explanation_renders_in_english_by_default():
    banana = find_commodity("banana")
    result = predict_shelf_life(banana, 36, lang="en")
    assert not _has_devanagari(result["explanation"])
    assert not _has_devanagari(result["disclaimer"])
    assert "36" in result["explanation"]


def test_explanation_renders_in_hindi():
    banana = find_commodity("banana")
    result = predict_shelf_life(banana, 36, lang="hi")
    assert _has_devanagari(result["explanation"])
    assert _has_devanagari(result["disclaimer"])


def test_explanation_hindi_for_equal_and_cooler_cases_too():
    banana = find_commodity("banana")
    for temp in [25, 15]:
        result = predict_shelf_life(banana, temp, lang="hi")
        assert _has_devanagari(result["explanation"]), temp


def test_clamped_explanation_suffix_renders_in_hindi():
    banana = find_commodity("banana")
    result = predict_shelf_life(banana, -40, lang="hi")
    assert result["was_clamped"] is True
    assert _has_devanagari(result["explanation"])


# ---------------------------------------------------------------------------
# Plain recommend() unaffected, ranking/scoring unaffected
# ---------------------------------------------------------------------------


def test_plain_recommend_has_no_shelf_life_prediction_field():
    result = recommend("banana", ambient_temperature_c=36)
    assert "shelf_life_prediction" not in result


def test_ranking_order_unaffected_by_shelf_life_prediction():
    without_temp = recommend_detailed("strawberry")
    with_temp = recommend_detailed("strawberry", ambient_temperature_c=36)
    ids_without = [r["material_id"] for r in without_temp["recommendations"]]
    ids_with = [r["material_id"] for r in with_temp["recommendations"]]
    assert ids_without == ids_with
    scores_without = [r["score"] for r in without_temp["recommendations"]]
    scores_with = [r["score"] for r in with_temp["recommendations"]]
    assert scores_without == scores_with


# ---------------------------------------------------------------------------
# API layer
# ---------------------------------------------------------------------------


def test_api_shelf_life_prediction_present_with_temperature():
    r = client.post("/recommend/detailed", json={"commodity_id": "banana", "ambient_temperature_c": 36})
    assert r.status_code == 200
    d = r.json()
    assert d["shelf_life_prediction"] is not None
    assert d["shelf_life_prediction"]["predicted_shelf_life_days"] > 0


def test_api_shelf_life_prediction_null_without_temperature():
    r = client.post("/recommend/detailed", json={"commodity_id": "banana"})
    assert r.status_code == 200
    assert r.json()["shelf_life_prediction"] is None


def test_api_shelf_life_prediction_hindi():
    r = client.post(
        "/recommend/detailed", json={"commodity_id": "banana", "ambient_temperature_c": 36, "lang": "hi"}
    )
    d = r.json()
    assert _has_devanagari(d["shelf_life_prediction"]["explanation"])


def test_api_plain_recommend_has_no_shelf_life_prediction_field():
    r = client.post("/recommend", json={"commodity_id": "banana", "ambient_temperature_c": 36})
    assert "shelf_life_prediction" not in r.json()
