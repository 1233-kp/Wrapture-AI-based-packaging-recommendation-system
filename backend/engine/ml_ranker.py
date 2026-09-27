"""Loads the trained ML ranker and scores materials at inference time.

This is a SECOND, corroborating signal alongside the rules engine's score —
never a replacement. See recommend_detailed() in recommender.py for how the
two are combined: the rules engine's score still drives ranking and all
user-facing explanations (match_breakdown, trade_off_summary); this module
only adds an `ml_confidence_score` annotation and an agreement note.

Uses training.features.encode_features() — the exact same function
training/generate_training_data.py used to build the training rows — so
there is no train/serve skew between how a feature vector was built during
training versus here at request time.
"""

from pathlib import Path
from typing import Any

import joblib
import numpy as np

from training.features import FEATURE_NAMES, encode_features

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "material_ranker.joblib"

_model = None
_feature_names: list[str] | None = None
_load_error: str | None = None


def _ensure_loaded() -> bool:
    """Loads the model once, lazily. Returns True if a usable model is
    loaded. Missing/unreadable model file is NOT fatal — see is_available()
    and how recommend_detailed() treats ml_confidence_score as optional."""
    global _model, _feature_names, _load_error
    if _model is not None or _load_error is not None:
        return _model is not None
    try:
        bundle = joblib.load(MODEL_PATH)
        _model = bundle["model"]
        _feature_names = bundle["feature_names"]
        if _feature_names != FEATURE_NAMES:
            # The saved model was trained against a different feature schema
            # than the current code expects — refuse to serve predictions
            # from it rather than silently feeding it misaligned columns.
            _load_error = "Model file's feature schema doesn't match the current FEATURE_NAMES."
            _model = None
    except (FileNotFoundError, KeyError, EOFError) as exc:
        _load_error = f"Could not load ML ranker model: {exc}"
    return _model is not None


def is_available() -> bool:
    return _ensure_loaded()


def predict_score(commodity: dict, material: dict, rules: dict, budget_tier: str, prioritize_sustainability: bool) -> float | None:
    """Returns a 0-100-ish predicted score, or None if no model is loaded.
    Clamped to [0, 100] since a RandomForest can occasionally extrapolate
    slightly outside the training label range on unusual inputs."""
    if not _ensure_loaded():
        return None
    features = encode_features(commodity, material, rules, budget_tier, prioritize_sustainability)
    vector = np.array([[features[name] for name in FEATURE_NAMES]])
    prediction = float(_model.predict(vector)[0])
    return round(max(0.0, min(100.0, prediction)), 1)


def build_agreement_note(
    top_pick_material_id: str, scored_candidates: list[dict], lang: str = "en"
) -> dict[str, Any] | None:
    """Compares the rules engine's #1 pick against which candidate the ML
    model scored highest among the SAME shortlist (the top_n already chosen
    by the rules engine — this is a corroboration check on the rules
    engine's own shortlist, not an independent full re-ranking of all 13
    materials). Returns None if no candidate has an ml_confidence_score."""
    from engine.i18n_strings import t

    scored = [c for c in scored_candidates if c.get("ml_confidence_score") is not None]
    if not scored:
        return None

    ml_top_pick = max(scored, key=lambda c: c["ml_confidence_score"])
    agrees = ml_top_pick["material_id"] == top_pick_material_id

    if agrees:
        note = t("ml_agreement_agrees", lang)
    else:
        note = t("ml_agreement_disagrees", lang, material_name=ml_top_pick["material_name"])

    return {
        "agrees": agrees,
        "ml_top_pick_material_id": ml_top_pick["material_id"],
        "note": note,
    }
