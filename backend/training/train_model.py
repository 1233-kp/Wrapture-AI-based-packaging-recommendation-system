"""Trains the ML ranker and validates it with GroupKFold cross-validation.

=============================================================================
WHY GROUPKFOLD, GROUPED BY base_commodity_id
=============================================================================
A plain random K-Fold split would put different synthetic variations of the
SAME real commodity (e.g. "tomato_synth_3" in train, "tomato_synth_11" in
test) on both sides of the split. Since those variations share the same
category, similar moisture/fat/pH neighborhoods, and the same rules-engine
formula generated both labels, a model could score deceptively well on the
test fold just by having "seen tomato before" in a slightly different guise
— target leakage, not genuine generalization.

GroupKFold, grouped by base_commodity_id, makes that structurally impossible:
every row descending from a given real commodity — all 260 of them — goes
entirely into ONE fold. A test fold's commodities are ones the model has
literally never seen in any form during that fold's training. This is the
same rigor a competing team's README described using GroupKFold CV to avoid
exactly this leakage trap, and it's why this script reports per-fold
metrics honestly rather than one optimistic pooled number.
=============================================================================

Run with: python -m training.train_model  (from /backend)
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold

from engine.recommender import _materials, _rules, find_commodity
from evaluation.reference_cases import REFERENCE_CASES
from training.features import FEATURE_NAMES, encode_features

DATA_PATH = Path(__file__).resolve().parent / "data" / "training_data.csv"
MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_PATH = MODELS_DIR / "material_ranker.joblib"
METRICS_PATH = MODELS_DIR / "model_metrics.json"

N_FOLDS = 5
RANDOM_SEED = 42


def _build_model() -> RandomForestRegressor:
    # Modest depth/leaf-size on purpose: an unconstrained RandomForest can
    # memorize synthetic-generation noise rather than the underlying pattern,
    # regardless of dataset size. These are deliberately conservative, not
    # tuned for a leaderboard score. See model_metrics.json -> dataset for the
    # row/feature counts from the last training run.
    return RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=4,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )


def run_group_kfold_cv(X: np.ndarray, y: np.ndarray, groups: np.ndarray) -> dict:
    gkf = GroupKFold(n_splits=N_FOLDS)
    fold_metrics = []

    for fold_i, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups)):
        train_groups = set(groups[train_idx])
        test_groups = set(groups[test_idx])
        assert train_groups.isdisjoint(test_groups), "GroupKFold leaked a commodity group across train/test"

        model = _build_model()
        model.fit(X[train_idx], y[train_idx])
        preds = model.predict(X[test_idx])

        r2 = r2_score(y[test_idx], preds)
        mae = mean_absolute_error(y[test_idx], preds)
        fold_metrics.append(
            {
                "fold": fold_i,
                "n_train": int(len(train_idx)),
                "n_test": int(len(test_idx)),
                "n_test_groups": len(test_groups),
                "r2": round(float(r2), 4),
                "mae": round(float(mae), 4),
            }
        )
        print(f"Fold {fold_i}: n_test={len(test_idx)} ({len(test_groups)} commodities) R2={r2:.4f} MAE={mae:.3f}")

    avg_r2 = float(np.mean([m["r2"] for m in fold_metrics]))
    avg_mae = float(np.mean([m["mae"] for m in fold_metrics]))
    print(f"\nGroupKFold average: R2={avg_r2:.4f} MAE={avg_mae:.3f}")

    return {
        "n_folds": N_FOLDS,
        "grouped_by": "base_commodity_id",
        "per_fold": fold_metrics,
        "avg_r2": round(avg_r2, 4),
        "avg_mae": round(avg_mae, 4),
    }


def evaluate_against_reference_set(final_model: RandomForestRegressor) -> dict:
    """Independent sanity check: for each hand-curated reference case (real
    commodities, real food-science-grounded expected materials — see
    evaluation/reference_cases.py for the current count), predict a score for
    every real material using the FINAL model and see whether the model's own
    top-1/top-3 picks land in the expected set. This is our best proxy for
    real-world validity, since the training labels themselves are rules-
    engine-derived, not independently lab-verified — a strong result here
    means the model's learned approximation still lines up with the same
    general food-science judgment the rules engine (and our own curation)
    encode, not proof of scientific correctness in an absolute sense.

    Note this evaluates the model on REAL, exact commodity property values —
    not synthetic perturbations — so it's a genuinely different input
    distribution point than most training rows, even though the model did
    see OTHER synthetic variations descended from the same 30 anchors during
    training (unlike the GroupKFold folds above, which withhold entire
    commodities). Report both numbers; don't conflate them.
    """
    rules = _rules()
    materials = _materials()

    top1_hits = 0
    top3_hits = 0
    mismatches = []

    for case in REFERENCE_CASES:
        commodity = find_commodity(case.commodity_id)
        if commodity is None:
            continue

        budget_tier = case.conditions.get("budget_tier", "standard")
        budget_tier = {"economy": "low", "standard": "medium", "premium": "high"}.get(budget_tier, budget_tier)
        prioritize_sustainability = case.conditions.get("prioritize_sustainability", False)

        scored = []
        for material in materials:
            feats = encode_features(commodity, material, rules, budget_tier, prioritize_sustainability)
            vector = np.array([[feats[name] for name in FEATURE_NAMES]])
            pred = final_model.predict(vector)[0]
            scored.append((material["id"], pred))
        scored.sort(key=lambda pair: pair[1], reverse=True)

        top1 = scored[0][0]
        top3 = {m for m, _ in scored[:3]}

        top1_hit = top1 in case.expected_material_ids
        top3_hit = bool(top3 & case.expected_material_ids)
        top1_hits += int(top1_hit)
        top3_hits += int(top3_hit)

        if not top1_hit:
            mismatches.append(
                {
                    "case_id": case.case_id,
                    "commodity_id": case.commodity_id,
                    "expected": sorted(case.expected_material_ids),
                    "ml_top1": top1,
                    "ml_top3": sorted(top3),
                }
            )

    total = len(REFERENCE_CASES)
    return {
        "total_cases": total,
        "top1_agreement_pct": round(100 * top1_hits / total, 1),
        "top3_agreement_pct": round(100 * top3_hits / total, 1),
        "mismatches": mismatches,
        "caveat": (
            "This measures agreement between the ML model's predictions and the same "
            "hand-curated, food-science-grounded reference set used to evaluate the rules "
            "engine (see evaluation/run_evaluation.py) — NOT independent lab validation. "
            "Both the rules engine and this model's training labels ultimately trace back "
            "to the same encoded heuristics; a high score here means the model learned a "
            "faithful approximation of those heuristics, not that the heuristics themselves "
            "are scientifically proven."
        ),
    }


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    X = df[FEATURE_NAMES].to_numpy()
    y = df["label_score"].to_numpy()
    groups = df["base_commodity_id"].to_numpy()

    print(f"Loaded {len(df)} rows, {len(set(groups))} commodity groups, {len(FEATURE_NAMES)} features.\n")

    print("=== GroupKFold cross-validation (grouped by base_commodity_id) ===")
    cv_results = run_group_kfold_cv(X, y, groups)

    print("\n=== Training final model on all data ===")
    final_model = _build_model()
    final_model.fit(X, y)

    print(f"\n=== Independent check against the {len(REFERENCE_CASES)}-case hand-curated reference set ===")
    reference_results = evaluate_against_reference_set(final_model)
    print(f"Top-1 agreement: {reference_results['top1_agreement_pct']}%")
    print(f"Top-3 agreement: {reference_results['top3_agreement_pct']}%")

    feature_importances = sorted(
        zip(FEATURE_NAMES, final_model.feature_importances_.tolist()),
        key=lambda pair: pair[1],
        reverse=True,
    )
    print("\n=== Feature importances (top 10) ===")
    for name, importance in feature_importances[:10]:
        print(f"  {name:35s} {importance:.4f}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": final_model, "feature_names": FEATURE_NAMES}, MODEL_PATH)
    print(f"\nSaved model to {MODEL_PATH}")

    metrics = {
        "dataset": {
            "n_rows": len(df),
            "n_commodity_groups": len(set(groups)),
            "n_features": len(FEATURE_NAMES),
            "provenance": (
                f"Synthetic — {len(set(groups))} real commodities as anchors, perturbed property "
                "variations labeled by the rules engine's own _score_material(). See "
                "training/generate_training_data.py and training/README.md."
            ),
        },
        "model": {"type": "RandomForestRegressor", "params": _build_model().get_params()},
        "group_kfold_cv": cv_results,
        "reference_set_agreement": reference_results,
        "feature_importances": [{"feature": n, "importance": round(i, 4)} for n, i in feature_importances],
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics to {METRICS_PATH}")


if __name__ == "__main__":
    main()
