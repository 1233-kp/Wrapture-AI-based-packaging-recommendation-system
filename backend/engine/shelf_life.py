"""Q10-based, temperature-adjusted shelf-life PREDICTION.

The Q10 temperature coefficient method is a real, well-established food-science
technique for approximating how a reaction rate (here, spoilage) scales with
temperature:

    predicted_shelf_life_days = typical_shelf_life_days * Q10 ** ((reference_temp - actual_temp) / 10)

This is layered on top of each commodity's EXISTING typical_ambient_shelf_life_days
midpoint (data/commodities.json) — it does not introduce a new per-commodity number,
only a category-level temperature adjustment to the number we already have. See
data/shelf_life_rules.json's _meta for why Q10/reference-temperature are CATEGORY-level
(not per-commodity — we have no per-commodity kinetic data) and why the reference
temperature is ~25C (ambient) for every category except frozen_foods.

Deliberately independent of any particular material: unlike estimated_shelf_life_days
(computed per-material in engine/recommender.py, adjusted for that material's barrier
quality), this is a single, material-independent fact about the commodity at a given
storage temperature — surfaced as a top-level field in /recommend/detailed, not
duplicated identically across every recommendation candidate.

Deliberately self-contained w.r.t. engine.recommender — no import from it here, for the
same circular-import reason documented in engine/compliance_check.py and
training/features.py. `rules` (this module's own shelf_life_rules.json, not
recommender.py's rules.json) is loaded locally.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from engine.i18n_strings import t

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache
def _shelf_life_rules() -> dict:
    with open(DATA_DIR / "shelf_life_rules.json", encoding="utf-8") as f:
        return json.load(f)


def _midpoint(range_dict: dict[str, float] | None) -> float | None:
    if not range_dict:
        return None
    return (range_dict["min"] + range_dict["max"]) / 2


def predict_shelf_life(
    commodity: dict, actual_storage_temp_c: float | None, lang: str = "en"
) -> dict[str, Any] | None:
    """Returns {predicted_shelf_life_days, shelf_life_confidence, explanation,
    was_clamped, disclaimer} — or None if a prediction can't be made.

    Returns None (field omitted, never a fabricated default) when:
    - no storage temperature was supplied (actual_storage_temp_c is None) — this
      calculation only runs when the user actually gave us a temperature to work with;
    - the commodity has no typical_ambient_shelf_life_days baseline to adjust; or
    - the commodity's category isn't in shelf_life_rules.json's category table.
    """
    if actual_storage_temp_c is None:
        return None

    typical_shelf_life = _midpoint(commodity.get("typical_ambient_shelf_life_days"))
    if typical_shelf_life is None:
        return None

    config = _shelf_life_rules()
    category_config = config["categories"].get(commodity["category"])
    if category_config is None:
        return None

    q10 = category_config["q10_factor"]
    reference_temp = category_config["reference_temperature_c"]

    exponent = (reference_temp - actual_storage_temp_c) / 10
    raw_predicted = typical_shelf_life * (q10**exponent)

    clamp = config["_meta"]["clamp"]
    min_days = clamp["min_days"]
    max_days = typical_shelf_life * clamp["max_multiplier"]
    clamped_predicted = max(min_days, min(max_days, raw_predicted))
    was_clamped = clamped_predicted != raw_predicted

    predicted_rounded = round(clamped_predicted, 1)
    typical_rounded = round(typical_shelf_life, 1)
    temp_str = f"{actual_storage_temp_c:g}"
    reference_str = f"{reference_temp:g}"

    if actual_storage_temp_c == reference_temp:
        explanation = t(
            "shelf_life_explanation_equal", lang, temp=temp_str, reference=reference_str, days=predicted_rounded
        )
    elif actual_storage_temp_c > reference_temp:
        explanation = t(
            "shelf_life_explanation_warmer",
            lang,
            temp=temp_str,
            reference=reference_str,
            days=predicted_rounded,
            typical=typical_rounded,
        )
    else:
        explanation = t(
            "shelf_life_explanation_cooler",
            lang,
            temp=temp_str,
            reference=reference_str,
            days=predicted_rounded,
            typical=typical_rounded,
        )

    if was_clamped:
        explanation += t("shelf_life_clamped_suffix", lang)

    return {
        "predicted_shelf_life_days": predicted_rounded,
        "shelf_life_confidence": category_config["confidence"],
        "explanation": explanation,
        "was_clamped": was_clamped,
        "disclaimer": t("shelf_life_disclaimer", lang),
    }
