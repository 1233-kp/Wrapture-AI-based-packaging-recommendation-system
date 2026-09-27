"""Tests for engine/cold_chain.py — cold-chain temperature-excursion
re-recommendation. Uses the same banana fixture (fresh_fruit, Q10=2.2,
25C reference) as test_shelf_life.py, and reuses recommend_detailed() to
build realistic report["recommendation"] payloads rather than hand-rolling
fake ones.
"""

import copy

from engine.cold_chain import URGENT_THRESHOLD_HOURS, recalculate_after_excursion
from engine.recommender import recommend_detailed


def _has_devanagari(text: str) -> bool:
    return any("ऀ" <= ch <= "ॿ" for ch in text)


def _report_with_temp(temp_c=25):
    return {"recommendation": recommend_detailed("banana", ambient_temperature_c=temp_c)}


def _report_without_temp():
    return {"recommendation": recommend_detailed("banana")}


# ---------------------------------------------------------------------------
# Core math: mild vs. severe excursions
# ---------------------------------------------------------------------------


def test_mild_excursion_barely_changes_remaining_shelf_life():
    """A small temperature bump for a short duration should leave most of
    the shelf life intact and not trigger the urgent action."""
    report = _report_with_temp()
    baseline_days = report["recommendation"]["shelf_life_prediction"]["predicted_shelf_life_days"]

    result = recalculate_after_excursion(report, temperature_reached_c=27, duration_hours=1)

    assert result is not None
    assert result["remaining_shelf_life_days"] > baseline_days * 0.8
    assert result["action_urgent"] is False


def test_severe_excursion_sharply_reduces_remaining_shelf_life():
    """A hot, long excursion should sharply cut remaining shelf life and
    trigger the urgent action message."""
    report = _report_with_temp()
    baseline_days = report["recommendation"]["shelf_life_prediction"]["predicted_shelf_life_days"]

    result = recalculate_after_excursion(report, temperature_reached_c=40, duration_hours=48)

    assert result is not None
    assert result["remaining_shelf_life_days"] < baseline_days * 0.3
    assert result["action_urgent"] is True


def test_severe_excursion_never_goes_negative():
    report = _report_with_temp()
    result = recalculate_after_excursion(report, temperature_reached_c=45, duration_hours=500)
    assert result["remaining_shelf_life_days"] == 0.0
    assert result["remaining_shelf_life_hours"] == 0.0


def test_severe_excursion_uses_expired_message_not_zero_hours():
    """'Sell within 0.0 hours' would read as nonsensical — a fully-elapsed
    remaining shelf life should get a distinct, clearer message."""
    report = _report_with_temp()
    result = recalculate_after_excursion(report, temperature_reached_c=45, duration_hours=500)
    assert result["action_urgent"] is True
    assert "0.0 hours" not in result["action_message"]
    assert "already elapsed" in result["action_message"]


def test_urgent_threshold_boundary():
    """Sanity check that action_urgent tracks URGENT_THRESHOLD_HOURS, not
    a hardcoded number that could drift out of sync."""
    report = _report_with_temp()
    # A duration engineered to land just over vs. just under the threshold.
    baseline_days = report["recommendation"]["shelf_life_prediction"]["predicted_shelf_life_days"]
    just_over = recalculate_after_excursion(
        report, temperature_reached_c=25, duration_hours=baseline_days * 24 - URGENT_THRESHOLD_HOURS + 1
    )
    just_under = recalculate_after_excursion(
        report, temperature_reached_c=25, duration_hours=baseline_days * 24 - URGENT_THRESHOLD_HOURS - 1
    )
    assert just_over["action_urgent"] is True
    assert just_under["action_urgent"] is False


# ---------------------------------------------------------------------------
# The excursion calc always reuses predict_shelf_life() fresh on the real
# commodity — it doesn't re-derive off the report's own prior prediction
# (that would double-apply the Q10 adjustment when the excursion temp
# matches the original one; see the round-trip test below).
# ---------------------------------------------------------------------------


def test_round_trip_at_the_same_temperature_with_zero_duration_is_a_no_op():
    """Logging an 'excursion' at the exact same temperature the report was
    originally predicted at, with zero elapsed duration, should reproduce
    that same original prediction exactly — not double-apply Q10."""
    report = _report_with_temp(temp_c=15)  # cooler than reference -> a non-trivial adjustment
    original_prediction = report["recommendation"]["shelf_life_prediction"]["predicted_shelf_life_days"]

    result = recalculate_after_excursion(report, temperature_reached_c=15, duration_hours=0)

    assert result["remaining_shelf_life_days"] == round(original_prediction, 2)


def test_result_does_not_depend_on_whether_the_report_had_a_prior_prediction():
    """A report saved without an ambient temperature (no shelf_life_prediction
    field) should give the same excursion result as one saved with a
    temperature — the calc always uses the commodity's real typical shelf
    life via predict_shelf_life(), not whatever the report happened to
    predict originally."""
    with_temp = _report_with_temp()
    without_temp = _report_without_temp()
    assert without_temp["recommendation"]["shelf_life_prediction"] is None

    result_with = recalculate_after_excursion(with_temp, temperature_reached_c=27, duration_hours=1)
    result_without = recalculate_after_excursion(without_temp, temperature_reached_c=27, duration_hours=1)

    assert result_with["remaining_shelf_life_days"] == result_without["remaining_shelf_life_days"]


# ---------------------------------------------------------------------------
# Original report data is never mutated
# ---------------------------------------------------------------------------


def test_original_report_is_not_mutated():
    report = _report_with_temp()
    before = copy.deepcopy(report)

    recalculate_after_excursion(report, temperature_reached_c=40, duration_hours=48)

    assert report == before


def test_repeated_calls_are_independent_not_cumulative():
    """Logging two excursions back to back shouldn't compound off of each
    other's output unless the caller explicitly re-feeds the result — each
    call is computed fresh from the same original report."""
    report = _report_with_temp()
    first = recalculate_after_excursion(report, temperature_reached_c=30, duration_hours=2)
    second = recalculate_after_excursion(report, temperature_reached_c=30, duration_hours=2)
    assert first["remaining_shelf_life_days"] == second["remaining_shelf_life_days"]


# ---------------------------------------------------------------------------
# Missing/unusable data -> None, never a fabricated number
# ---------------------------------------------------------------------------


def test_report_with_no_commodity_id_returns_none():
    result = recalculate_after_excursion({"recommendation": {}}, temperature_reached_c=25, duration_hours=1)
    assert result is None


def test_report_with_unknown_commodity_id_returns_none():
    report = {"recommendation": {"commodity": {"id": "not-a-real-commodity"}}}
    result = recalculate_after_excursion(report, temperature_reached_c=25, duration_hours=1)
    assert result is None


# ---------------------------------------------------------------------------
# English/Hindi
# ---------------------------------------------------------------------------


def test_explanation_and_action_message_render_in_hindi():
    report = _report_with_temp()
    result = recalculate_after_excursion(report, temperature_reached_c=40, duration_hours=48, lang="hi")
    assert _has_devanagari(result["explanation"])
    assert _has_devanagari(result["action_message"])
    assert _has_devanagari(result["disclaimer"])


def test_ok_action_message_renders_in_hindi():
    report = _report_with_temp()
    result = recalculate_after_excursion(report, temperature_reached_c=27, duration_hours=1, lang="hi")
    assert result["action_urgent"] is False
    assert _has_devanagari(result["action_message"])
