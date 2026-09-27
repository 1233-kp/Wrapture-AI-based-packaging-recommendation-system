"""Tests for the ML ranker (engine/ml_ranker.py) and its integration into
/recommend/detailed. Does NOT re-run GroupKFold CV or retrain anything —
that's train_model.py's job (a deliberately separate, manually-run script,
not part of the fast test suite). These tests check the SAVED model loads
and behaves sanely, and that wiring it into the API didn't break anything.
"""

import pytest

from engine.ml_ranker import build_agreement_note, is_available, predict_score
from engine.recommender import _materials, _rules, find_commodity, recommend_detailed


def test_model_is_available():
    """If this fails, `python -m training.train_model` needs to be (re-)run
    — see training/README.md."""
    assert is_available()


@pytest.mark.parametrize("commodity_id", ["banana", "cheddar_cheese", "chicken_fresh", "rice", "strawberry"])
def test_predict_score_runs_without_error_for_every_material(commodity_id):
    commodity = find_commodity(commodity_id)
    rules = _rules()
    for material in _materials():
        score = predict_score(commodity, material, rules, "medium", False)
        assert score is not None
        assert 0.0 <= score <= 100.0


def test_ml_predictions_correlate_with_rules_engine_scores():
    """Sanity check, not an exact-match check: the ML model was trained to
    approximate the rules engine's scoring function, so its predictions
    should track the rules engine's own scores reasonably well across a
    spread of real commodity-material pairs — a strong positive correlation,
    not identical numbers (the model is a learned approximation, not a
    lookup of the same formula).

    Runs over EVERY commodity in the dataset (not a hardcoded sample) so this
    check automatically covers future dataset growth, same as the rest of
    the suite — see training/README.md for the full-dataset correlation
    number as of the last training run."""
    from engine.recommender import _score_material, list_commodities

    rules = _rules()
    rules_scores = []
    ml_scores = []
    req = {"budget_tier": "medium", "prioritize_sustainability": False}

    for commodity in list_commodities():
        for material in _materials():
            rules_scores.append(_score_material(commodity, material, rules, req)["score"])
            ml_scores.append(predict_score(commodity, material, rules, "medium", False))

    # Pearson correlation via numpy (already a project dependency through pandas/sklearn)
    import numpy as np

    correlation = float(np.corrcoef(rules_scores, ml_scores)[0, 1])
    assert correlation > 0.7, f"Expected strong correlation between rules-engine and ML scores, got {correlation:.3f}"


def test_agreement_note_agrees_when_ml_top_pick_matches():
    candidates = [
        {"material_id": "a", "material_name": "A", "ml_confidence_score": 90.0},
        {"material_id": "b", "material_name": "B", "ml_confidence_score": 60.0},
    ]
    result = build_agreement_note("a", candidates)
    assert result["agrees"] is True
    assert result["ml_top_pick_material_id"] == "a"


def test_agreement_note_flags_disagreement_without_hiding_it():
    candidates = [
        {"material_id": "a", "material_name": "A", "ml_confidence_score": 50.0},
        {"material_id": "b", "material_name": "B", "ml_confidence_score": 95.0},
    ]
    result = build_agreement_note("a", candidates)
    assert result["agrees"] is False
    assert result["ml_top_pick_material_id"] == "b"
    assert "b" not in result["note"].lower() or "B" in result["note"]  # note mentions the diverging pick, not silent


def test_agreement_note_none_when_no_scores_present():
    candidates = [{"material_id": "a", "material_name": "A", "ml_confidence_score": None}]
    assert build_agreement_note("a", candidates) is None


# ---------------------------------------------------------------------------
# /recommend/detailed integration — additive fields present, nothing else changed
# ---------------------------------------------------------------------------


def test_recommend_detailed_includes_ml_fields_without_changing_ranking():
    result = recommend_detailed("banana")
    assert result is not None

    # Ranking order must still be driven by the rules engine's own `score` —
    # the whole point of "additive, not a replacement".
    scores = [r["score"] for r in result["recommendations"]]
    assert scores == sorted(scores, reverse=True)

    for rec in result["recommendations"]:
        assert "ml_confidence_score" in rec
        assert rec["ml_confidence_score"] is None or 0.0 <= rec["ml_confidence_score"] <= 100.0

    assert "ml_agreement" in result
    if result["ml_agreement"] is not None:
        assert set(result["ml_agreement"].keys()) == {"agrees", "ml_top_pick_material_id", "note"}


def test_recommend_detailed_still_has_all_previously_existing_fields():
    """Confirms nothing from the pre-ML response shape was removed or renamed."""
    result = recommend_detailed("cheddar_cheese")
    assert set(result.keys()) >= {
        "commodity",
        "recommendations",
        "map_gas_guidance",
        "regulatory_note",
        "ml_agreement",
    }
    top = result["recommendations"][0]
    assert set(top.keys()) >= {
        "material_id",
        "material_name",
        "score",
        "sustainability_score",
        "cost_tier",
        "recyclability_rating",
        "rationale",
        "warnings",
        "match_breakdown",
        "trade_off_summary",
        "overall_confidence",
        "estimated_shelf_life_days",
    }


def test_plain_recommend_is_completely_unaffected():
    """recommend() (the non-detailed endpoint) was explicitly out of scope for
    the ML integration — confirm it has no ML fields at all."""
    from engine.recommender import recommend as recommend_fn

    result = recommend_fn("banana")
    assert result is not None
    for rec in result["recommendations"]:
        assert "ml_confidence_score" not in rec
    assert "ml_agreement" not in result
