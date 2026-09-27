"""Generates the synthetic training dataset for the ML ranker.

=============================================================================
WHAT THIS IS AND WHY IT'S A DEFENSIBLE WAY TO GET TRAINING DATA
=============================================================================
We only have a few dozen real commodities (see data/commodities.json for the
current count). Training a model directly on one row per real
commodity-material pair would just teach the model to memorize a lookup
table — with that few distinct commodity "points" in feature space, a tree
model has no reason to learn the actual functional relationship between,
say, moisture content and the ideal WVTR target; it can just as easily
overfit to a handful of arbitrary coordinates. That's not meaningfully
different from the rules engine it's supposedly complementing.

So instead: for each real commodity (the "anchor"), we generate many
synthetic VARIATIONS — the same commodity's properties (moisture, fat, pH,
shelf life), each independently perturbed within a plausible real-world band
around the anchor's own stated range. "Tomato" stops being one fixed point
(93-95% moisture) and becomes a distribution the model has to learn to
handle continuously (moisture ranging roughly 88-99%, fat/pH/shelf-life
likewise perturbed). Respiration class is a genuine discrete trait of the
produce type, so it's kept fixed per anchor except for a small chance of
shifting one step (representing cultivar/ripeness variation), not perturbed
like a continuous number would be.

The LABEL for every synthetic row is computed by calling the real rules
engine's own _score_material() — the same function backend/engine/recommender.py
uses for real recommendations. This is legitimate, not circular, for one
specific reason: the rules engine is a deterministic FORMULA encoding real
food-packaging-science heuristics (documented, reviewed, evaluated against
our hand-curated reference set — see evaluation/). Using it to label a much
wider, continuous input space than the fixed anchor points it was hand-tuned
against is a way of teaching a model the PATTERN the formula encodes —
"moisture trades off against WVTR target this way," "respiration class
shifts the ideal OTR band that way" — not a list of memorized answers. The
model is learning to approximate a known function across its domain, the
same way you'd generate training data for any surrogate/distillation model
of a deterministic simulator.

What this does NOT do: introduce any information the rules engine didn't
already encode. The ML model's ceiling is bounded by how well it learns to
approximate the rules engine's own formula — it cannot discover packaging
science the rules engine doesn't already know. That's exactly why
GroupKFold validation (train_model.py) and the independent check against the
hand-curated reference set matter: they're the only ways to tell whether the
model actually generalizes the pattern, versus overfitting to synthetic noise.
=============================================================================
"""

import csv
import random
from pathlib import Path

from engine.recommender import _materials, _rules, _score_material, list_commodities
from training.features import encode_features

RANDOM_SEED = 42
VARIATIONS_PER_COMMODITY = 20
OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "training_data.csv"

BUDGET_TIERS = ["low", "medium", "high"]
RESPIRATION_STEPS = [None, "low", "moderate", "high", "very_high"]


def _perturb_range(range_dict: dict | None, rel_margin: float, floor: float = 0.0, ceiling: float | None = None) -> float:
    """Samples one point uniformly from [min, max] extended by rel_margin on
    each side, clipped to [floor, ceiling]. Returns 0.0 if range_dict is None
    (matches _midpoint's behavior elsewhere for commodities with no value in
    that field, e.g. non-fatty dry goods with a near-zero fat range)."""
    if not range_dict:
        return 0.0
    lo, hi = range_dict["min"], range_dict["max"]
    width = hi - lo
    margin = max(width * rel_margin, width * 0.1 + 0.01)  # a floor on the margin so a near-zero-width range still varies
    lo_ext, hi_ext = lo - margin, hi + margin
    value = random.uniform(lo_ext, hi_ext)
    value = max(floor, value)
    if ceiling is not None:
        value = min(ceiling, value)
    return round(value, 3)


def _maybe_shift_respiration(base_class: str | None) -> str | None:
    """~15% chance of shifting one respiration step, representing natural
    cultivar/ripeness variation — kept small and directional-neutral since
    this is a genuine discrete trait, not something to perturb freely."""
    if base_class is None:
        return None  # non-produce commodities don't gain a respiration rate
    if random.random() > 0.15:
        return base_class
    idx = RESPIRATION_STEPS.index(base_class)
    shift = random.choice([-1, 1])
    new_idx = max(1, min(len(RESPIRATION_STEPS) - 1, idx + shift))  # stays within low..very_high
    return RESPIRATION_STEPS[new_idx]


def _make_synthetic_commodity(anchor: dict, variation_index: int) -> dict:
    moisture = _perturb_range(anchor.get("moisture_content_percent"), rel_margin=0.15, floor=0.0, ceiling=100.0)
    fat = _perturb_range(anchor.get("fat_content_percent"), rel_margin=0.2, floor=0.0, ceiling=100.0)
    ph = _perturb_range(anchor.get("ph_range"), rel_margin=0.1, floor=0.0, ceiling=14.0)
    shelf_life = _perturb_range(anchor.get("typical_ambient_shelf_life_days"), rel_margin=0.3, floor=0.1)
    respiration = _maybe_shift_respiration(anchor.get("respiration_rate_class"))

    return {
        "id": f"{anchor['id']}_synth_{variation_index}",
        "name": f"{anchor['name']} (synthetic variant {variation_index})",
        "category": anchor["category"],  # category is the commodity's TYPE — not perturbed, it anchors the group
        "moisture_content_percent": {"min": moisture, "max": moisture},
        "fat_content_percent": {"min": fat, "max": fat},
        "ph_range": {"min": ph, "max": ph},
        "respiration_rate_class": respiration,
        "typical_ambient_shelf_life_days": {"min": shelf_life, "max": shelf_life},
        "confidence": anchor.get("confidence", "medium"),
        # Grouping key for GroupKFold — the REAL anchor commodity this row descends
        # from. This is what "grouped by the original commodity" means: no fold may
        # ever see two rows with the same base_commodity_id split across train/test.
        "base_commodity_id": anchor["id"],
    }


def generate_rows() -> list[dict]:
    random.seed(RANDOM_SEED)
    rules = _rules()
    materials = _materials()
    anchors = list_commodities()

    rows: list[dict] = []
    for anchor in anchors:
        for variation_index in range(VARIATIONS_PER_COMMODITY):
            synthetic_commodity = _make_synthetic_commodity(anchor, variation_index)
            budget_tier = random.choice(BUDGET_TIERS)
            prioritize_sustainability = random.random() < 0.3

            req = {"budget_tier": budget_tier, "prioritize_sustainability": prioritize_sustainability}

            for material in materials:
                label = _score_material(synthetic_commodity, material, rules, req)["score"]
                features = encode_features(synthetic_commodity, material, rules, budget_tier, prioritize_sustainability)
                rows.append(
                    {
                        "base_commodity_id": anchor["id"],  # GroupKFold group column
                        "material_id": material["id"],
                        **features,
                        "label_score": label,
                    }
                )
    return rows


def main() -> None:
    rows = generate_rows()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(rows[0].keys())
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    n_groups = len({r["base_commodity_id"] for r in rows})
    print(f"Generated {len(rows)} rows across {n_groups} base-commodity groups.")
    print(f"Wrote to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
