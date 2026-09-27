"""Lightweight, rule-based regulatory-compliance FLAGS — not a compliance
engine. Evaluates the small hand-curated rule set in
data/compliance_rules.json against a (commodity, material) pair and
returns a list of informational notes.

Purely informational and purely additive: nothing here reads into or
writes back to _score_material's ranking/scoring path in
engine/recommender.py. A material with 3 compliance flags scores and
ranks EXACTLY the same as if it had zero — these notes are surfaced
alongside the existing recommendation, never folded into it.

See data/compliance_rules.json's _meta for the grounding/confidence
discipline these rules follow, and COMPLIANCE_DISCLAIMER below for the
disclaimer that must always accompany any non-empty result.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from engine.i18n_strings import t

# Deliberately self-contained w.r.t. engine.recommender — no import from it here. This
# module is imported BY engine/recommender.py (engine.recommender -> engine.compliance_check),
# so importing back from engine.recommender would create a circular import (same class of
# issue documented in training/features.py). rules is instead taken as a parameter by
# evaluate_compliance() rather than loaded internally. engine.i18n_strings is safe to
# import here since it has no dependency on engine.recommender either way.
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def compliance_disclaimer(lang: str = "en") -> str:
    return t("compliance_disclaimer", lang)


@lru_cache
def _compliance_rules() -> list[dict]:
    with open(DATA_DIR / "compliance_rules.json", encoding="utf-8") as f:
        return json.load(f)["rules"]


def _is_commodity_acidic(commodity: dict, rules: dict) -> bool:
    ph_range = commodity.get("ph_range")
    if not ph_range:
        return False
    return ph_range["max"] < rules["thresholds"]["acidic_ph_max"]


def _rule_applies(rule: dict, commodity: dict, material: dict, rules: dict) -> bool:
    trigger = rule["trigger"]
    trigger_type = trigger["type"]
    values = trigger["values"]

    if trigger_type == "material_id_in":
        return material["id"] in values
    if trigger_type == "material_category_in":
        return material["category"] in values
    if trigger_type == "material_id_in_and_commodity_acidic":
        return material["id"] in values and _is_commodity_acidic(commodity, rules)
    if trigger_type == "material_breathable_and_commodity_category_in":
        return bool(material.get("breathable")) and commodity.get("category") in values

    # Unknown trigger type: fail closed (don't flag) rather than crash — a
    # future rules.json edit with a typo'd trigger type shouldn't 500 the
    # whole recommendation endpoint over an informational add-on.
    return False


def evaluate_compliance(commodity: dict, material: dict, rules: dict, lang: str = "en") -> list[dict[str, Any]]:
    """Returns a list of {rule_id, description, confidence, general_reference}
    dicts for every compliance rule that applies to this commodity+material
    pair. Empty list if none apply — that's an expected, common outcome for
    plenty of materials (e.g. glass triggers none of the current rules).

    `rules` is the same rules.json dict the caller (engine/recommender.py)
    already has loaded — passed in rather than loaded here, to keep this
    module import-independent of engine.recommender (see note above).

    `description` is looked up via engine.i18n_strings' t() using a
    "compliance_<rule_id>" key, so it renders in the requested language —
    same hand-authored-parallel-template pattern as every other dynamic
    sentence in this project, not live translation. `general_reference`
    intentionally stays as the raw compliance_rules.json string in every
    language: it names a regulatory body/framework (e.g. "FSSAI Packaging &
    Labelling Regulations"), not a sentence to translate."""
    notes = []
    for rule in _compliance_rules():
        if _rule_applies(rule, commodity, material, rules):
            notes.append(
                {
                    "rule_id": rule["id"],
                    "description": t(f"compliance_{rule['id']}", lang),
                    "confidence": rule["confidence"],
                    "general_reference": rule["general_reference"],
                }
            )
    return notes
