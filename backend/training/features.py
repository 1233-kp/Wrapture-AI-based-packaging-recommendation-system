"""Shared feature encoding for the ML ranker.

Imported by BOTH generate_training_data.py (labels) and engine/ml_ranker.py
(live inference) — there is exactly one function that turns
(commodity, material, conditions) into a feature vector. That's deliberate:
the single most common way an ML pipeline silently breaks is training and
serving encoding the same inputs differently ("train/serve skew"). Having
one shared function makes that class of bug structurally impossible instead
of something we have to remember to keep in sync by hand.

Feature choices are intentionally limited to what the rules engine's own
_score_material() actually consumes for its numeric score — see that
function in engine/recommender.py for the ground truth. Two request fields
that DO exist on /recommend/detailed (expected_transport_days,
ambient_temperature_c) are deliberately EXCLUDED here: they only affect
warning text in the rules engine, never the numeric score, so including them
would just teach the model two permanently-zero-importance features.
"""

from __future__ import annotations

# Deliberately self-contained — no import from engine.recommender here. This module is
# imported BY engine/ml_ranker.py (engine -> training), so importing back from
# engine.recommender would create a circular import (training -> engine -> training).
# _midpoint and the sustainability-keyword lookup are tiny (a few lines each); duplicating
# them here keeps the dependency direction a clean one-way DAG instead of tangling engine
# and training together. If engine/recommender.py's versions ever change meaningfully,
# update both — they're intentionally kept minimal to make that low-risk.


def _midpoint(range_dict: dict | None) -> float | None:
    if not range_dict:
        return None
    return (range_dict["min"] + range_dict["max"]) / 2


def _sustainability_score(recyclability_rating: str, rules: dict) -> float:
    rating_lower = recyclability_rating.lower()
    for entry in rules["sustainability_score_by_recyclability_keyword"]:
        if entry["keyword"] in rating_lower:
            return entry["score"]
    return rules["default_sustainability_score"]

MATERIAL_CATEGORIES = [
    "flexible_film",
    "flexible_film_or_rigid",
    "rigid_or_film",
    "flexible_film_laminate",
    "rigid",
    "rigid_paper",
]

COMMODITY_CATEGORIES = [
    "fresh_fruit",
    "fresh_vegetable",
    "dairy",
    "dry_goods_grains",
    "spices",
    "meat_fish",
    "bakery",
    "nuts_dried_fruits",
    "beverages",
    "frozen_foods",
    "ready_to_eat_snacks",
]

# None (no respiration_rate_class at all, i.e. not fresh produce) sits below
# "low" — ordinal, not one-hot, because there's a genuine natural ordering
# (higher class = more actively respiring) that a tree model can split on
# sensibly at either end.
RESPIRATION_ORDER = {None: 0, "low": 1, "moderate": 2, "high": 3, "very_high": 4}

BUDGET_TIER_ORDER = {"low": 0, "medium": 1, "high": 2}

# Fixed column order — both generate_training_data.py and ml_ranker.py must
# produce rows in exactly this order, since the trained model has no concept
# of column names, only column position.
FEATURE_NAMES = (
    [
        "commodity_moisture_pct",
        "commodity_fat_pct",
        "commodity_ph",
        "commodity_respiration_ord",
        "commodity_shelf_life_days",
        "material_otr",
        "material_wvtr",
        "material_thickness",
        "material_cost_ord",
        "material_breathable",
        "material_sustainability_pts",
        "material_practicality_pts",
        "budget_tier_ord",
        "prioritize_sustainability",
    ]
    + [f"commodity_category_{c}" for c in COMMODITY_CATEGORIES]
    + [f"material_category_{c}" for c in MATERIAL_CATEGORIES]
)


def _practicality_points(material: dict, rules: dict) -> float:
    config = rules.get("packaging_format_practicality", {})
    return config.get("overrides", {}).get(material["id"], config.get("default_score", 9))


def encode_features(
    commodity: dict,
    material: dict,
    rules: dict,
    budget_tier: str,
    prioritize_sustainability: bool,
) -> dict[str, float]:
    """Returns a {feature_name: value} dict covering every name in
    FEATURE_NAMES exactly once — the single source of truth for how a
    (commodity, material, conditions) triple becomes a model input."""
    cost_tier_score = rules["cost_tier_score"]
    cost_order = {"low": cost_tier_score.get("low", 10), "medium": cost_tier_score.get("medium", 6), "high": cost_tier_score.get("high", 3)}

    row: dict[str, float] = {
        "commodity_moisture_pct": _midpoint(commodity.get("moisture_content_percent")) or 0.0,
        "commodity_fat_pct": _midpoint(commodity.get("fat_content_percent")) or 0.0,
        "commodity_ph": _midpoint(commodity.get("ph_range")) or 7.0,
        "commodity_respiration_ord": RESPIRATION_ORDER.get(commodity.get("respiration_rate_class"), 0),
        "commodity_shelf_life_days": _midpoint(commodity.get("typical_ambient_shelf_life_days")) or 0.0,
        "material_otr": _midpoint(material["otr_cm3_m2_day_atm"]),
        "material_wvtr": _midpoint(material["wvtr_g_m2_day"]),
        "material_thickness": _midpoint(material["thickness_range_micron"]),
        "material_cost_ord": cost_order.get(material["cost_tier"], 6),
        "material_breathable": 1.0 if material.get("breathable") else 0.0,
        "material_sustainability_pts": _sustainability_score(material["recyclability_rating"], rules),
        "material_practicality_pts": _practicality_points(material, rules),
        "budget_tier_ord": BUDGET_TIER_ORDER.get(budget_tier, 1),
        "prioritize_sustainability": 1.0 if prioritize_sustainability else 0.0,
    }

    for cat in COMMODITY_CATEGORIES:
        row[f"commodity_category_{cat}"] = 1.0 if commodity.get("category") == cat else 0.0
    for cat in MATERIAL_CATEGORIES:
        row[f"material_category_{cat}"] = 1.0 if material.get("category") == cat else 0.0

    return row


def feature_row_to_vector(row: dict[str, float]) -> list[float]:
    """Orders an encode_features() dict into the fixed FEATURE_NAMES column order."""
    return [row[name] for name in FEATURE_NAMES]
