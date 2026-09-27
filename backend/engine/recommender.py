"""Rules-based scoring engine: ranks packaging materials for a given commodity.

Loads three JSON reference files (commodities, packaging materials, rules) once
at import time and exposes `recommend()` and `recommend_detailed()` as the entry
points used by the API layer. All scoring logic lives here so it can be
unit-tested without spinning up FastAPI.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from engine.i18n_strings import (
    COMMODITY_CATEGORY_WORD,
    COST_TIER_WORD,
    COST_TOLERANCE_WORD,
    DETAILED_BUDGET_TIER_WORD,
    MATERIAL_CATEGORY_WORD,
    OTR_REASON_WORD,
    RESPIRATION_CLASS_WORD,
    t,
    word,
)
from engine.compliance_check import compliance_disclaimer as _compliance_disclaimer_text
from engine.compliance_check import evaluate_compliance
from engine.government_scheme import government_scheme_note
from engine.material_lookup import find_material
from engine.ml_ranker import build_agreement_note, predict_score
from engine.shelf_life import predict_shelf_life

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_CONFIDENCE_ORDER = {"low": 1, "medium": 2, "high": 3}
_COST_ORDER = {"low": 1, "medium": 2, "high": 3}

# Maps the user-facing budget tier vocabulary used by /recommend/detailed onto
# the low/medium/high tier the scoring weights already understand.
_BUDGET_TIER_ALIASES = {
    "economy": "low",
    "standard": "medium",
    "premium": "high",
    "low": "low",
    "medium": "medium",
    "high": "high",
}


def _load_json(filename: str) -> dict:
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def _commodities() -> list[dict]:
    return _load_json("commodities.json")["commodities"]


@lru_cache
def _materials() -> list[dict]:
    return _load_json("packaging_materials.json")["materials"]


@lru_cache
def _rules() -> dict:
    return _load_json("rules.json")


def _midpoint(range_dict: dict[str, float] | None) -> float | None:
    if not range_dict:
        return None
    return (range_dict["min"] + range_dict["max"]) / 2


def find_commodity(commodity_id_or_name: str) -> dict | None:
    needle = commodity_id_or_name.strip().lower()
    for c in _commodities():
        if c["id"].lower() == needle or c["name"].lower() == needle:
            return c
    return None


def list_commodities() -> list[dict]:
    return _commodities()


def _score_component(actual: float, target_max: float) -> tuple[float, bool]:
    """Returns (fraction in [0,1], meets_target). Full credit at or under the
    target; credit decays smoothly as the actual value exceeds it."""
    if actual <= target_max:
        return 1.0, True
    # Decays to ~0.1 once actual is 3x the target; never hits exactly 0 so a
    # material is never *disqualified* purely by this component.
    ratio = target_max / actual
    return max(0.1, ratio), False


def _fit_label(fraction: float) -> str:
    if fraction >= 0.85:
        return "good"
    if fraction >= 0.5:
        return "partial"
    return "poor"


def _weaker_confidence(a: str, b: str) -> str:
    """Returns whichever of two confidence levels is less certain, so a
    recommendation never looks more authoritative than its weakest input."""
    return a if _CONFIDENCE_ORDER.get(a, 2) <= _CONFIDENCE_ORDER.get(b, 2) else b


def _sustainability_score(recyclability_rating: str, rules: dict) -> float:
    """0-10 scale based on keyword match against the material's recyclability
    rating text; see rules.json for the keyword -> score table."""
    rating_lower = recyclability_rating.lower()
    for entry in rules["sustainability_score_by_recyclability_keyword"]:
        if entry["keyword"] in rating_lower:
            return entry["score"]
    return rules["default_sustainability_score"]


def _score_material(commodity: dict, material: dict, rules: dict, req: dict, lang: str = "en") -> dict:
    thresholds = rules["thresholds"]
    wvtr_targets = rules["wvtr_targets_g_m2_day"]
    otr_targets = rules["otr_targets_cm3_m2_day_atm"]
    respiration_bands = rules["respiration_otr_bands"]

    weights = dict(rules["weights"])
    if req.get("prioritize_sustainability"):
        weights["sustainability_fit"] *= 3
    budget_tier = req.get("budget_tier", "medium")
    if budget_tier == "low":
        weights["cost_fit"] *= 2
    elif budget_tier == "high":
        weights["cost_fit"] *= 0.5

    rationale: list[str] = []
    warnings: list[str] = []
    # Structured, per-dimension breakdown for explainability: which commodity
    # property was compared against which packaging property, and how well it fit.
    components: list[dict] = []

    moisture_mid = _midpoint(commodity.get("moisture_content_percent"))
    fat_mid = _midpoint(commodity.get("fat_content_percent"))
    material_wvtr_mid = _midpoint(material["wvtr_g_m2_day"])
    material_otr_mid = _midpoint(material["otr_cm3_m2_day_atm"])

    # -- moisture fit: high-moisture commodities generally need a low-WVTR (moisture-tight)
    # material so they don't dry out. Exception: respiring fresh produce continuously releases
    # its own moisture/CO2, so a tight moisture barrier causes condensation and rot instead of
    # protecting shelf life — for those, permeability is governed by respiration_fit below, and
    # this component falls back to a lenient default so it doesn't fight that rule.
    #
    # Second exception, same shape as oxygen_fit's category check below: a dried/cured/
    # intermediate-moisture product in a moisture_sensitive_category (currently just meat_fish)
    # sits in the gap between "high moisture" and "low moisture" purely by number (e.g. dried
    # fish at ~20%) but still needs a tight barrier — moisture re-uptake risks microbial
    # regrowth in a preserved protein, not just staleness. Without this, that gap fell through
    # to the lenient default target meant for goods like bread or cheese. See rules.json's
    # moisture_sensitive_categories note for the full reasoning.
    is_respiring_produce = bool(commodity.get("respiration_rate_class"))
    moisture_sensitive_category = commodity["category"] in rules.get("moisture_sensitive_categories", {}).get(
        "categories", []
    )
    if is_respiring_produce:
        wvtr_target = wvtr_targets["default_max_wvtr"]
    elif moisture_mid is not None and moisture_mid >= thresholds["high_moisture_percent"]:
        wvtr_target = wvtr_targets["high_moisture_commodity_max_wvtr"]
    elif moisture_mid is not None and moisture_mid < thresholds["low_moisture_percent"]:
        wvtr_target = wvtr_targets["low_moisture_commodity_max_wvtr"]
    elif moisture_sensitive_category:
        wvtr_target = wvtr_targets["high_moisture_commodity_max_wvtr"]
    else:
        wvtr_target = wvtr_targets["default_max_wvtr"]
    moisture_frac, moisture_ok = _score_component(material_wvtr_mid, wvtr_target)
    if moisture_ok:
        rationale.append(
            t(
                "moisture_fit_rationale",
                lang,
                wvtr=f"{material_wvtr_mid:g}",
                moisture=f"{moisture_mid:.0f}%",
                target=wvtr_target,
            )
        )
    else:
        warnings.append(
            t("moisture_fit_warning", lang, wvtr=f"{material_wvtr_mid:g}", target=wvtr_target)
        )
    components.append(
        {
            "dimension": "moisture_barrier",
            "commodity_property": (
                t("moisture_property_known", lang, moisture=f"{moisture_mid:.0f}%")
                if moisture_mid is not None
                else t("moisture_property_unknown", lang)
            ),
            "packaging_property": t(
                "moisture_packaging_property", lang, wvtr=f"{material_wvtr_mid:g}", target=wvtr_target
            ),
            "fit": _fit_label(moisture_frac),
            "weight": weights["moisture_fit"],
            "explanation": (
                t("moisture_explanation_ok", lang) if moisture_ok else t("moisture_explanation_not_ok", lang)
            ),
        }
    )

    # -- oxygen fit: a tight O2 barrier matters for more than one reason, so the target
    # tightens for whichever reason applies — high fat content (oxidative rancidity) OR
    # category-level sensitivity (aroma retention for ground spices; raw-protein freshness,
    # color, and microbial safety for meat/fish, which isn't a fat-oxidation mechanism at
    # all). Without the category check, a cheap low-barrier material could win purely
    # because a non-fatty spice or lean cut of meat didn't trip the fat threshold.
    #
    # Exception, same reasoning as moisture_fit above: actively-respiring produce needs
    # permeability governed by respiration_fit and respiration_class_packaging_boost, not by
    # oxygen_fit's "low OTR prevents rancidity" assumption — that assumption is about sealed
    # shelf-stable goods, not a fresh vegetable that needs to breathe. Without this exception,
    # oxygen_fit actively fought the breathability boost: it penalized intentionally-high-OTR
    # vented/perforated materials as if their permeability were a barrier defect, wiping out
    # the boost's effect (caught when strawberry/spinach still ranked plain HDPE top-1 after
    # the boost was added — see evaluation/run_evaluation.py).
    high_fat = fat_mid is not None and fat_mid >= thresholds["high_fat_percent"]
    oxygen_sensitive_category = commodity["category"] in rules.get("oxygen_sensitive_categories", {}).get(
        "categories", []
    )
    if is_respiring_produce and not high_fat:
        oxygen_frac, oxygen_ok = 1.0, True
        otr_target = None
        otr_target_reason = "not_applicable"
    elif high_fat:
        otr_target = otr_targets["high_fat_commodity_max_otr"]
        otr_target_reason = "high-fat"
        oxygen_frac, oxygen_ok = _score_component(material_otr_mid, otr_target)
    elif oxygen_sensitive_category:
        otr_target = otr_targets["category_sensitive_max_otr"]
        otr_target_reason = "category"
        oxygen_frac, oxygen_ok = _score_component(material_otr_mid, otr_target)
    else:
        otr_target = otr_targets["default_max_otr"]
        otr_target_reason = "default"
        oxygen_frac, oxygen_ok = _score_component(material_otr_mid, otr_target)

    if otr_target_reason == "not_applicable":
        pass  # governed by respiration_fit / respiration_class_packaging_boost instead
    elif oxygen_ok:
        template_key = "oxygen_rationale_high_fat" if high_fat else "oxygen_rationale_general"
        rationale.append(t(template_key, lang, otr=f"{material_otr_mid:g}", target=otr_target))
    elif high_fat:
        warnings.append(
            t(
                "oxygen_warning_high_fat",
                lang,
                otr=f"{material_otr_mid:g}",
                fat=f"{fat_mid:.0f}%",
            )
        )
    elif oxygen_sensitive_category:
        warnings.append(
            t(
                "oxygen_warning_category",
                lang,
                otr=f"{material_otr_mid:g}",
                category=word(COMMODITY_CATEGORY_WORD, commodity["category"], lang),
            )
        )
    components.append(
        {
            "dimension": "oxygen_barrier",
            "commodity_property": (
                t("oxygen_property_known", lang, fat=f"{fat_mid:.1f}%")
                if fat_mid is not None
                else t("oxygen_property_unknown", lang)
            ),
            "packaging_property": (
                t("otr_value", lang, otr=f"{material_otr_mid:g}")
                + (t("target_suffix", lang, target=otr_target) if otr_target is not None else "")
            ),
            "fit": "not_applicable" if otr_target_reason == "not_applicable" else _fit_label(oxygen_frac),
            "weight": weights["oxygen_fit"],
            "explanation": (
                t("oxygen_explanation_not_applicable", lang)
                if otr_target_reason == "not_applicable"
                else (
                    t("oxygen_explanation_ok", lang)
                    if oxygen_ok
                    else t(
                        "oxygen_explanation_not_ok",
                        lang,
                        reason=word(OTR_REASON_WORD, otr_target_reason, lang),
                    )
                )
            ),
        }
    )

    # -- respiration fit: only applies to fresh produce; a near-total O2 barrier can
    # suffocate produce and trigger anaerobic fermentation, so this is not just "lower is better"
    respiration_class = commodity.get("respiration_rate_class")
    if respiration_class and respiration_class in respiration_bands:
        band = respiration_bands[respiration_class]
        respiration_class_word = word(RESPIRATION_CLASS_WORD, respiration_class, lang)
        if band["min_otr"] <= material_otr_mid <= band["max_otr"]:
            respiration_frac = 1.0
            rationale.append(
                t("respiration_rationale_match", lang, otr=f"{material_otr_mid:g}", cls=respiration_class_word)
            )
            respiration_explanation = t("respiration_explanation_match", lang)
        elif material_otr_mid < band["min_otr"]:
            # too tight a barrier for a respiring product
            respiration_frac = max(0.1, material_otr_mid / band["min_otr"])
            warnings.append(t("respiration_warning_too_tight", lang, cls=respiration_class_word))
            respiration_explanation = t("respiration_explanation_tight", lang)
        else:
            respiration_frac = max(0.1, band["max_otr"] / material_otr_mid)
            warnings.append(t("respiration_warning_too_loose", lang, cls=respiration_class_word))
            respiration_explanation = t("respiration_explanation_loose", lang)
        components.append(
            {
                "dimension": "respiration_compatibility",
                "commodity_property": t(
                    "respiration_property",
                    lang,
                    cls=respiration_class_word,
                    min=band["min_otr"],
                    max=band["max_otr"],
                ),
                "packaging_property": t("otr_value", lang, otr=f"{material_otr_mid:g}"),
                "fit": _fit_label(respiration_frac),
                "weight": weights["respiration_fit"],
                "explanation": respiration_explanation,
            }
        )
    else:
        # Not produce: this dimension doesn't apply, so don't let it drag the score down.
        respiration_frac = 1.0
        components.append(
            {
                "dimension": "respiration_compatibility",
                "commodity_property": t("respiration_property_na", lang),
                "packaging_property": "n/a",
                "fit": "not_applicable",
                "weight": weights["respiration_fit"],
                "explanation": t("respiration_explanation_na", lang),
            }
        )

    # -- respiration packaging boost: explicit reward for materials tagged breathable=true
    # (see packaging_materials.json), separate from respiration_fit's numeric OTR-range check
    # above. A material can land inside the respiration_otr_bands range purely by coincidence
    # of its own bulk resin permeability (plain LDPE is naturally quite permeable) without
    # actually being a vented/perforated product engineered for produce airflow — this rewards
    # the deliberate design choice specifically, so a purpose-built option doesn't keep losing
    # to a cheap resin that only numerically resembles the right permeability.
    boost_config = rules.get("respiration_class_packaging_boost", {})
    boost_weight = boost_config.get("weight", 0)
    boost_applicable = respiration_class in boost_config.get("classes", [])
    is_breathable = bool(material.get("breathable"))
    if boost_applicable:
        breathability_frac = 1.0 if is_breathable else 0.2
        respiration_class_word = word(RESPIRATION_CLASS_WORD, respiration_class, lang)
        if is_breathable:
            rationale.append(t("boost_rationale", lang, cls=respiration_class_word))
        else:
            warnings.append(t("boost_warning", lang, cls=respiration_class_word))
        breathability_explanation = (
            t("boost_explanation_tagged", lang) if is_breathable else t("boost_explanation_not_tagged", lang)
        )
    else:
        breathability_frac = 1.0
        breathability_explanation = t("boost_explanation_na", lang)
    components.append(
        {
            "dimension": "respiration_packaging_boost",
            "commodity_property": (
                t("boost_property_applicable", lang, cls=word(RESPIRATION_CLASS_WORD, respiration_class, lang))
                if boost_applicable
                else t("boost_property_na", lang)
            ),
            "packaging_property": (
                t("boost_packaging_tagged", lang) if is_breathable else t("boost_packaging_not_tagged", lang)
            ),
            "fit": _fit_label(breathability_frac) if boost_applicable else "not_applicable",
            "weight": boost_weight,
            "explanation": breathability_explanation,
        }
    )

    # -- category fit
    preferred_categories = rules["category_preferred_material_categories"].get(commodity["category"], [])
    if material["category"] in preferred_categories:
        category_frac = 1.0
        rationale.append(
            t(
                "category_rationale",
                lang,
                material_cat=word(MATERIAL_CATEGORY_WORD, material["category"], lang),
                commodity_cat=word(COMMODITY_CATEGORY_WORD, commodity["category"], lang),
            )
        )
        category_explanation = t("category_explanation_match", lang)
    else:
        category_frac = 0.4
        category_explanation = t("category_explanation_no_match", lang)
    components.append(
        {
            "dimension": "category_fit",
            "commodity_property": t(
                "category_commodity_property", lang, category=word(COMMODITY_CATEGORY_WORD, commodity["category"], lang)
            ),
            "packaging_property": t(
                "category_packaging_property", lang, category=word(MATERIAL_CATEGORY_WORD, material["category"], lang)
            ),
            "fit": _fit_label(category_frac),
            "weight": weights["category_fit"],
            "explanation": category_explanation,
        }
    )

    # -- cost fit
    cost_frac = rules["cost_tier_score"].get(material["cost_tier"], 5) / 10.0
    internal_tier = req.get("budget_tier", "medium")
    material_tier_word = word(COST_TIER_WORD, material["cost_tier"], lang)
    # /recommend/detailed accepts economy/standard/premium and maps it internally to
    # low/medium/high for scoring purposes (see _BUDGET_TIER_ALIASES). Displaying the
    # internal low/medium/high word as if it were the literal requested value was
    # misleading (e.g. a "premium" request showing up as "Requested budget tier: High")
    # — when recommend_detailed() gave us the original requested label, show both the
    # literal request AND what it maps to, instead of silently substituting one for
    # the other. Falls back to the plain internal-tier label when there's no separate
    # requested label to show (e.g. the plain /recommend endpoint, whose own vocabulary
    # already IS low/medium/high, so there's nothing to translate in the first place).
    requested_tier_label = req.get("requested_tier_label")
    if requested_tier_label:
        cost_commodity_property = t(
            "cost_commodity_property_mapped",
            lang,
            label=word(DETAILED_BUDGET_TIER_WORD, requested_tier_label, lang),
            tolerance=word(COST_TOLERANCE_WORD, internal_tier, lang),
        )
    else:
        cost_commodity_property = t("cost_commodity_property", lang, tier=word(COST_TIER_WORD, internal_tier, lang))
    components.append(
        {
            "dimension": "cost",
            "commodity_property": cost_commodity_property,
            "packaging_property": t("cost_packaging_property", lang, tier=material_tier_word),
            "fit": _fit_label(cost_frac),
            "weight": weights["cost_fit"],
            "explanation": t("cost_explanation", lang, tier=material_tier_word),
        }
    )

    # -- sustainability fit
    sustainability_points = _sustainability_score(material["recyclability_rating"], rules)
    sustainability_frac = sustainability_points / 10.0
    if req.get("prioritize_sustainability") and sustainability_points >= 8:
        rationale.append(t("sustainability_rationale", lang, rating=material["recyclability_rating"]))
    components.append(
        {
            "dimension": "sustainability",
            "commodity_property": (
                t("sustainability_property_priority", lang)
                if req.get("prioritize_sustainability")
                else t("sustainability_property_standard", lang)
            ),
            "packaging_property": material["recyclability_rating"],
            "fit": _fit_label(sustainability_frac),
            "weight": weights["sustainability_fit"],
            "explanation": t("sustainability_explanation", lang, rating=material["recyclability_rating"]),
        }
    )

    # -- packaging format practicality: a genuine physical-format factor (weight,
    # fragility, pallet/shelf density for high-volume retail) — separate from barrier
    # performance and cost tier. Without this, a zero-permeability rigid material could
    # max out moisture/oxygen fit and still come out ahead on sustainability alone, with
    # cost tier as the only counterweight — not enough for everyday retail goods where a
    # flexible film/laminate with comparable practical barrier performance is the norm.
    practicality_config = rules.get("packaging_format_practicality", {})
    practicality_points = practicality_config.get("overrides", {}).get(
        material["id"], practicality_config.get("default_score", 9)
    )
    practicality_frac = practicality_points / 10.0
    if practicality_frac < 0.5:
        warnings.append(t("practicality_warning", lang, material_name=material["name"]))
    components.append(
        {
            "dimension": "format_practicality",
            "commodity_property": t("practicality_commodity_property", lang),
            "packaging_property": t(
                "practicality_packaging_property", lang, material_name=material["name"], points=practicality_points
            ),
            "fit": _fit_label(practicality_frac),
            "weight": weights["format_practicality_fit"],
            "explanation": (
                t("practicality_explanation_good", lang)
                if practicality_frac >= 0.85
                else t("practicality_explanation_poor", lang)
            ),
        }
    )

    fractions_and_weights = [
        (moisture_frac, weights["moisture_fit"]),
        (oxygen_frac, weights["oxygen_fit"]),
        (respiration_frac, weights["respiration_fit"]),
        (breathability_frac, boost_weight),
        (category_frac, weights["category_fit"]),
        (cost_frac, weights["cost_fit"]),
        (sustainability_frac, weights["sustainability_fit"]),
        (practicality_frac, weights["format_practicality_fit"]),
    ]
    total_weight = sum(w for _, w in fractions_and_weights)
    weighted_sum = sum(f * w for f, w in fractions_and_weights)
    score = (weighted_sum / total_weight) * 100 if total_weight else 0.0

    # -- hard compatibility flag: acidic foods + bare aluminum foil laminate corrode/react
    ph_range = commodity.get("ph_range")
    if ph_range and ph_range["max"] < thresholds["acidic_ph_max"]:
        if material["id"] in rules["acidic_incompatible_materials"]:
            score *= 0.5
            warnings.append(t("acidic_warning", lang, ph_max=ph_range["max"]))

    # -- confidence flagging: never let a recommendation look more certain than its
    # weakest underlying data point (commodity property estimate or material spec estimate).
    material_confidence = material.get("confidence", "medium")
    overall_confidence = _weaker_confidence(commodity.get("confidence", "medium"), material_confidence)

    # -- heuristic shelf-life estimate: NOT a lab-tested figure. A material that fully meets
    # this commodity's moisture/oxygen targets is treated as getting close to the commodity's
    # own typical ambient shelf-life ceiling; a poorer barrier fit pulls that estimate down.
    shelf_life = commodity.get("typical_ambient_shelf_life_days")
    if shelf_life:
        shelf_life_mid = (shelf_life["min"] + shelf_life["max"]) / 2
        barrier_quality = (moisture_frac + oxygen_frac) / 2
        estimated_shelf_life_days = round(shelf_life_mid * (0.5 + 0.5 * barrier_quality), 1)
    else:
        estimated_shelf_life_days = None

    return {
        "material_id": material["id"],
        "material_name": material["name"],
        "material_name_hi": material.get("display_name_hi"),
        "score": round(score, 1),
        "cost_tier": material["cost_tier"],
        "recyclability_rating": material["recyclability_rating"],
        "rationale": rationale,
        "warnings": warnings,
        # -- structured/explainable fields, used by recommend_detailed() --
        "components": components,
        "sustainability_score": round(sustainability_frac * 100, 1),
        "material_confidence": material_confidence,
        "overall_confidence": overall_confidence,
        "estimated_shelf_life_days": estimated_shelf_life_days,
    }


def _apply_condition_warnings(
    commodity: dict,
    recommendations: list[dict],
    expected_transport_days: float | None,
    ambient_temperature_c: float | None,
    lang: str = "en",
) -> None:
    """Appends warnings driven by request-time conditions (as opposed to the
    static commodity/material properties _score_material already covers)."""
    shelf_life = commodity.get("typical_ambient_shelf_life_days")
    if expected_transport_days is not None and shelf_life:
        if expected_transport_days > shelf_life["max"]:
            note = t(
                "condition_warning_transport",
                lang,
                days=f"{expected_transport_days:g}",
                min=shelf_life["min"],
                max=shelf_life["max"],
            )
            for r in recommendations:
                r["warnings"].append(note)

    if ambient_temperature_c is not None and ambient_temperature_c >= 30:
        respiration_class = commodity.get("respiration_rate_class")
        if respiration_class in ("high", "very_high"):
            note = t(
                "condition_warning_temperature",
                lang,
                temp=f"{ambient_temperature_c:g}",
                cls=word(RESPIRATION_CLASS_WORD, respiration_class, lang),
            )
            for r in recommendations:
                r["warnings"].append(note)


def _map_gas_guidance(commodity: dict, rules: dict, lang: str = "en") -> dict | None:
    """General MAP (Modified Atmosphere Packaging) starting-point gas mix for fresh
    produce, keyed off respiration rate class. Explicitly NOT commodity-specific
    lab-tested values — see the 'note' field, which the API always returns alongside it."""
    respiration_class = commodity.get("respiration_rate_class")
    table = rules.get("map_gas_guidance_by_respiration_class", {})
    if not respiration_class or respiration_class not in table:
        return {
            "applicable": False,
            "respiration_rate_class": respiration_class,
            "o2_percent": None,
            "co2_percent": None,
            "n2_percent": None,
            "note": t("map_gas_note_na", lang),
        }

    band = table[respiration_class]
    o2 = band["o2_percent"]
    co2 = band["co2_percent"]
    n2_min = round(100 - o2["max"] - co2["max"], 1)
    n2_max = round(100 - o2["min"] - co2["min"], 1)
    return {
        "applicable": True,
        "respiration_rate_class": respiration_class,
        "o2_percent": o2,
        "co2_percent": co2,
        "n2_percent": {"min": n2_min, "max": n2_max},
        "note": t("map_gas_note", lang),
    }


def _estimate_packaging_cost_per_unit(commodity: dict, material: dict, rules: dict) -> dict[str, float] | None:
    """Rough estimated cost (INR) to package 1 kg of this commodity in this material:
    the material's own per-kg price range (packaging_materials.json's
    estimated_cost_per_kg_inr) times a category-level estimate of how many grams of
    packaging material a kg of this commodity's category typically uses
    (rules.json's packaging_weight_g_per_kg_product_by_category), times a per-material
    weight_multiplier (packaging_materials.json's material_weight_multiplier) correcting
    for format/density differences the category-level estimate alone can't see — e.g. a
    glass jar genuinely uses more grams of material per kg of product than a thin film
    in the same commodity category, independent of which category that commodity is in.

    Purely informational — this is NOT read anywhere in _score_material, so it has
    zero effect on ranking or on budget_tier's existing directional scoring influence.
    Returns None if the material has no cost data (shouldn't happen for the current
    catalogue, but this stays defensive the same way estimated_shelf_life_days etc. do
    for missing commodity data).

    Still a rough estimate, not a guarantee: the category-level packaging-weight table
    and the material_weight_multiplier are both directional figures (see their
    confidence fields in packaging_materials.json / rules.json), not precise
    engineering data for a specific package design. The multiplier makes the result
    more directionally sound — glass no longer implausibly undercuts thin films — it
    doesn't make the number a quote.
    """
    cost_per_kg = material.get("estimated_cost_per_kg_inr")
    weight_multiplier = material.get("material_weight_multiplier")
    if not cost_per_kg or not weight_multiplier:
        return None
    weight_table = rules.get("packaging_weight_g_per_kg_product_by_category", {})
    weight_range = weight_table.get(commodity["category"], weight_table.get("default"))
    if not weight_range:
        return None
    cost_min = round(cost_per_kg["min"] * (weight_range["min"] / 1000) * weight_multiplier["min"], 2)
    cost_max = round(cost_per_kg["max"] * (weight_range["max"] / 1000) * weight_multiplier["max"], 2)
    return {"min": cost_min, "max": cost_max}


def _build_cost_comparison_note(
    candidate_cost: dict[str, float] | None,
    top_pick_cost: dict[str, float] | None,
    is_top_pick: bool,
    lang: str = "en",
) -> str | None:
    """Delta-style comparison against the top pick's estimated cost, same reasoning
    pattern as _build_trade_off_summary above — a percentage difference between this
    option's and the top pick's estimated cost midpoint."""
    if is_top_pick:
        return t("cost_comparison_reference", lang)
    if not candidate_cost or not top_pick_cost:
        return None

    c_mid = (candidate_cost["min"] + candidate_cost["max"]) / 2
    t_mid = (top_pick_cost["min"] + top_pick_cost["max"]) / 2
    if t_mid <= 0:
        return None

    pct = (c_mid - t_mid) / t_mid * 100
    if abs(pct) < 5:
        return t("cost_comparison_comparable", lang)
    template_key = "cost_comparison_more" if pct > 0 else "cost_comparison_less"
    return t(template_key, lang, pct=f"{abs(pct):.0f}")


_SENTENCE_END = {"en": ".", "hi": "।"}


def _build_trade_off_summary(candidate: dict, top_pick: dict, is_top_pick: bool, lang: str = "en") -> str:
    """Short, explicit trade-off phrase comparing this option to the #1-ranked pick,
    e.g. 'Cheaper than top pick, -3 days estimated shelf life'."""
    end = _SENTENCE_END.get(lang, ".")
    if is_top_pick:
        phrases = [t("trade_off_top_best_fit", lang)]
        phrases.append(t("trade_off_top_cost_tier", lang, tier=word(COST_TIER_WORD, candidate["cost_tier"], lang)))
        if candidate["sustainability_score"] >= 70:
            phrases.append(t("trade_off_top_good_recyclability", lang))
        return ", ".join(phrases) + end

    phrases: list[str] = []

    c_cost = _COST_ORDER.get(candidate["cost_tier"], 2)
    t_cost = _COST_ORDER.get(top_pick["cost_tier"], 2)
    if c_cost < t_cost:
        phrases.append(t("trade_off_cheaper", lang))
    elif c_cost > t_cost:
        phrases.append(t("trade_off_higher_cost", lang))

    c_life = candidate.get("estimated_shelf_life_days")
    t_life = top_pick.get("estimated_shelf_life_days")
    if c_life is not None and t_life is not None:
        delta = c_life - t_life
        if delta >= 1:
            phrases.append(t("trade_off_shelf_life_more", lang, delta=f"{delta:.0f}"))
        elif delta <= -1:
            phrases.append(t("trade_off_shelf_life_less", lang, delta=f"{delta:.0f}"))

    sus_delta = candidate["sustainability_score"] - top_pick["sustainability_score"]
    if sus_delta >= 20:
        phrases.append(t("trade_off_more_sustainable", lang))
    elif sus_delta <= -20:
        phrases.append(t("trade_off_less_sustainable", lang))

    if not phrases:
        phrases.append(t("trade_off_comparable", lang))

    first = phrases[0].capitalize() if lang == "en" else phrases[0]
    return first + (", " + ", ".join(phrases[1:]) if len(phrases) > 1 else "") + end


def recommend(
    commodity_id_or_name: str,
    budget_tier: str = "medium",
    prioritize_sustainability: bool = False,
    expected_transport_days: float | None = None,
    ambient_temperature_c: float | None = None,
    top_n: int = 3,
    lang: str = "en",
) -> dict[str, Any] | None:
    commodity = find_commodity(commodity_id_or_name)
    if commodity is None:
        return None

    rules = _rules()
    req = {
        "budget_tier": budget_tier,
        "prioritize_sustainability": prioritize_sustainability,
    }

    scored = [_score_material(commodity, material, rules, req, lang=lang) for material in _materials()]
    scored.sort(key=lambda r: r["score"], reverse=True)
    top = scored[:top_n]

    _apply_condition_warnings(commodity, top, expected_transport_days, ambient_temperature_c, lang=lang)

    return {
        "commodity": {
            "id": commodity["id"],
            "name": commodity["name"],
            "name_hi": commodity.get("display_name_hi"),
            "category": commodity["category"],
            "confidence": commodity["confidence"],
        },
        "recommendations": top,
        "disclaimer": t("disclaimer_basic", lang),
    }


def recommend_detailed(
    commodity_id_or_name: str,
    budget_tier: str = "standard",
    prioritize_sustainability: bool = False,
    expected_transport_days: float | None = None,
    ambient_temperature_c: float | None = None,
    top_n: int = 3,
    lang: str = "en",
) -> dict[str, Any] | None:
    """Same scoring as recommend(), enriched with: structured per-dimension
    match_breakdown, per-option trade_off_summary, 0-100 sustainability_score,
    confidence propagation, and commodity-level MAP gas guidance for produce."""
    commodity = find_commodity(commodity_id_or_name)
    if commodity is None:
        return None

    rules = _rules()
    internal_budget_tier = _BUDGET_TIER_ALIASES.get(budget_tier, "medium")
    req = {
        "budget_tier": internal_budget_tier,
        "prioritize_sustainability": prioritize_sustainability,
        # Only set when the caller passed the actual economy/standard/premium vocabulary
        # (what /recommend/detailed's own request schema restricts callers to) — None if
        # budget_tier was already a raw low/medium/high value, so the cost row's display
        # logic falls back to showing that value directly rather than a fabricated label.
        "requested_tier_label": budget_tier if budget_tier in DETAILED_BUDGET_TIER_WORD else None,
    }

    scored = [_score_material(commodity, material, rules, req, lang=lang) for material in _materials()]
    scored.sort(key=lambda r: r["score"], reverse=True)
    top = scored[:top_n]

    ml_agreement = None
    if top:
        top_pick = top[0]
        for i, candidate in enumerate(top):
            candidate["trade_off_summary"] = _build_trade_off_summary(
                candidate, top_pick, is_top_pick=(i == 0), lang=lang
            )
            # match_breakdown is just a clearer public name for the internal "components" field
            candidate["match_breakdown"] = candidate.pop("components")

            # -- ML ranker: a second, corroborating signal (see engine/ml_ranker.py).
            # Purely additive — never changes `top`'s order (already fixed above by the
            # rules engine's own score) or any existing field. None if no model is loaded.
            material = find_material(candidate["material_id"])
            candidate["ml_confidence_score"] = (
                predict_score(commodity, material, rules, internal_budget_tier, prioritize_sustainability)
                if material is not None
                else None
            )

            # -- estimated cost: informational only, computed from material price data
            # and a category-level packaging-weight estimate (see _estimate_packaging_cost_per_unit).
            # Does not touch _score_material, so budget_tier's existing directional ranking
            # influence is completely unaffected. top_pick is the SAME object as candidate
            # when i == 0, so its cost is already set by the time later iterations read it.
            candidate["estimated_cost_per_unit_inr"] = (
                _estimate_packaging_cost_per_unit(commodity, material, rules) if material is not None else None
            )
            candidate["cost_comparison_note"] = _build_cost_comparison_note(
                candidate["estimated_cost_per_unit_inr"],
                top_pick.get("estimated_cost_per_unit_inr"),
                is_top_pick=(i == 0),
                lang=lang,
            )

            # -- compliance flags: purely informational, evaluated against the same
            # rules-based engine/compliance_check.py for every candidate. Never read by
            # _score_material, so it has zero effect on ranking. Empty list is a normal,
            # common outcome (e.g. glass triggers none of the current rules).
            candidate["compliance_notes"] = (
                evaluate_compliance(commodity, material, rules, lang=lang) if material is not None else []
            )

        ml_agreement = build_agreement_note(top_pick["material_id"], top, lang=lang)

    _apply_condition_warnings(commodity, top, expected_transport_days, ambient_temperature_c, lang=lang)

    # Top-level disclaimer present only when at least one shown option actually has
    # compliance notes — matches the same "don't show it for nothing" spirit as the
    # frontend section being omitted entirely when a material has no notes.
    compliance_disclaimer = (
        _compliance_disclaimer_text(lang) if any(r.get("compliance_notes") for r in top) else None
    )

    # -- Q10 temperature-adjusted shelf-life prediction (engine/shelf_life.py) --
    # Material-independent (the calculation only uses the commodity's own typical
    # shelf life + category Q10 + the supplied storage temperature), so this is a
    # single top-level field, not duplicated per recommendation candidate. None
    # whenever ambient_temperature_c wasn't supplied — never a fabricated default.
    shelf_life_prediction = predict_shelf_life(commodity, ambient_temperature_c, lang=lang)

    return {
        "commodity": {
            "id": commodity["id"],
            "name": commodity["name"],
            "name_hi": commodity.get("display_name_hi"),
            "category": commodity["category"],
            "confidence": commodity["confidence"],
        },
        "recommendations": top,
        "map_gas_guidance": _map_gas_guidance(commodity, rules, lang=lang),
        "regulatory_note": t("regulatory_note", lang),
        "government_scheme_note": government_scheme_note(lang),
        "disclaimer": t("disclaimer_detailed", lang),
        "ml_agreement": ml_agreement,
        "compliance_disclaimer": compliance_disclaimer,
        "shelf_life_prediction": shelf_life_prediction,
    }
