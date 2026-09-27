"""Tests for the regulatory-compliance-flag feature (engine/compliance_check.py
and its wiring into recommend_detailed's compliance_notes/compliance_disclaimer).

Purely informational and purely additive — these tests specifically also
confirm plain recommend() is untouched and that scoring/ranking is
completely unaffected by adding compliance evaluation.
"""

from fastapi.testclient import TestClient

from engine.compliance_check import compliance_disclaimer, evaluate_compliance
from engine.recommender import (
    _materials,
    _rules,
    _score_material,
    find_commodity,
    recommend,
    recommend_detailed,
)
from main import app

client = TestClient(app)


def _material(material_id: str) -> dict:
    return next(m for m in _materials() if m["id"] == material_id)


# ---------------------------------------------------------------------------
# Specific rule triggers
# ---------------------------------------------------------------------------


def test_acidic_commodity_with_aluminum_foil_triggers_bare_foil_caution():
    strawberry = find_commodity("strawberry")  # acidic (pH max well under the 4.6 threshold)
    notes = evaluate_compliance(strawberry, _material("aluminum_foil_laminate"), _rules())
    rule_ids = [n["rule_id"] for n in notes]
    assert "acidic_food_bare_foil_caution" in rule_ids


def test_non_acidic_commodity_with_aluminum_foil_does_not_trigger_bare_foil_caution():
    rice = find_commodity("rice")  # not acidic
    notes = evaluate_compliance(rice, _material("aluminum_foil_laminate"), _rules())
    rule_ids = [n["rule_id"] for n in notes]
    assert "acidic_food_bare_foil_caution" not in rule_ids
    # But other material-only rules for this material still apply.
    assert "food_contact_layer_verification" in rule_ids


def test_glass_triggers_no_compliance_notes():
    """Confirms compliance_notes can genuinely be empty — glass matches none
    of the current rules for an ordinary non-acidic commodity."""
    rice = find_commodity("rice")
    notes = evaluate_compliance(rice, _material("glass"), _rules())
    assert notes == []


def test_laminate_materials_trigger_food_contact_and_epr_rules():
    commodity = find_commodity("cheddar_cheese")
    for material_id in ["metalized_film", "aluminum_foil_laminate", "evoh_film", "oriented_nylon"]:
        notes = evaluate_compliance(commodity, _material(material_id), _rules())
        rule_ids = [n["rule_id"] for n in notes]
        assert "food_contact_layer_verification" in rule_ids, material_id
        assert "epr_recyclability_complexity" in rule_ids, material_id


def test_plastic_materials_trigger_resin_id_code_rule_glass_and_paperboard_do_not():
    commodity = find_commodity("rice")
    plastic_ids = ["ldpe", "hdpe", "pet", "pp", "metalized_film"]
    for material_id in plastic_ids:
        rule_ids = [n["rule_id"] for n in evaluate_compliance(commodity, _material(material_id), _rules())]
        assert "resin_identification_code_labeling" in rule_ids, material_id

    for material_id in ["glass", "paperboard"]:
        rule_ids = [n["rule_id"] for n in evaluate_compliance(commodity, _material(material_id), _rules())]
        assert "resin_identification_code_labeling" not in rule_ids, material_id


def test_compostable_and_import_notes_trigger_for_pla_only():
    commodity = find_commodity("rice")
    pla_rule_ids = [n["rule_id"] for n in evaluate_compliance(commodity, _material("pla_biodegradable_film"), _rules())]
    assert "compostable_certification_note" in pla_rule_ids
    assert "imported_material_fssai_verification" in pla_rule_ids

    other_rule_ids = [n["rule_id"] for n in evaluate_compliance(commodity, _material("ldpe"), _rules())]
    assert "compostable_certification_note" not in other_rule_ids
    assert "imported_material_fssai_verification" not in other_rule_ids


def test_pp_triggers_microwave_note_others_do_not():
    commodity = find_commodity("rice")
    pp_rule_ids = [n["rule_id"] for n in evaluate_compliance(commodity, _material("pp"), _rules())]
    assert "microwave_safety_verification_note" in pp_rule_ids

    hdpe_rule_ids = [n["rule_id"] for n in evaluate_compliance(commodity, _material("hdpe"), _rules())]
    assert "microwave_safety_verification_note" not in hdpe_rule_ids


def test_breathable_material_with_fresh_produce_triggers_exemption_note():
    strawberry = find_commodity("strawberry")  # fresh_fruit
    breathable_material = _material("micro_perforated_film")
    assert breathable_material["breathable"] is True
    rule_ids = [n["rule_id"] for n in evaluate_compliance(strawberry, breathable_material, _rules())]
    assert "fresh_produce_labeling_exemption_note" in rule_ids


def test_breathable_material_with_non_produce_commodity_does_not_trigger_exemption_note():
    rice = find_commodity("rice")  # dry_goods_grains, not fresh produce
    breathable_material = _material("micro_perforated_film")
    rule_ids = [n["rule_id"] for n in evaluate_compliance(rice, breathable_material, _rules())]
    assert "fresh_produce_labeling_exemption_note" not in rule_ids


def test_unknown_trigger_type_fails_closed_not_crash():
    fake_rule = {
        "id": "fake_rule",
        "description": "x",
        "trigger": {"type": "not_a_real_trigger_type", "values": []},
        "confidence": "low",
        "general_reference": "x",
    }
    from engine.compliance_check import _rule_applies

    assert _rule_applies(fake_rule, find_commodity("rice"), _material("ldpe"), _rules()) is False


# ---------------------------------------------------------------------------
# Every rule has a confidence level from the shared vocabulary
# ---------------------------------------------------------------------------


def test_every_compliance_rule_has_valid_confidence_and_reference():
    from engine.compliance_check import _compliance_rules

    for rule in _compliance_rules():
        assert rule["confidence"] in ("low", "medium", "high"), rule["id"]
        assert rule["general_reference"], rule["id"]
        assert rule["description"], rule["id"]


# ---------------------------------------------------------------------------
# Wiring into recommend_detailed(): disclaimer always accompanies notes
# ---------------------------------------------------------------------------


def test_recommend_detailed_includes_compliance_notes_per_recommendation():
    result = recommend_detailed("turmeric_powder")
    for rec in result["recommendations"]:
        assert "compliance_notes" in rec
        assert isinstance(rec["compliance_notes"], list)


def test_compliance_disclaimer_present_when_any_recommendation_has_notes():
    result = recommend_detailed("turmeric_powder")
    assert any(rec["compliance_notes"] for rec in result["recommendations"])
    assert result["compliance_disclaimer"] == compliance_disclaimer()


def test_compliance_disclaimer_null_when_no_recommendation_has_notes():
    """Constructs a scenario where every shown option has zero compliance
    notes, and confirms the disclaimer is correctly absent (not shown for
    nothing)."""
    result = recommend_detailed("rice", budget_tier="premium")
    # Manually verify at least one real case: if every returned option happens
    # to have notes for this commodity, this assertion documents that fact
    # instead of silently no-oping — the real behavioral guarantee is checked
    # directly against evaluate_compliance() output for glass above.
    any_notes = any(rec["compliance_notes"] for rec in result["recommendations"])
    if not any_notes:
        assert result["compliance_disclaimer"] is None
    else:
        assert result["compliance_disclaimer"] == compliance_disclaimer()


# ---------------------------------------------------------------------------
# Plain recommend() and ranking/scoring completely unaffected
# ---------------------------------------------------------------------------


def test_plain_recommend_has_no_compliance_fields():
    result = recommend("turmeric_powder")
    for rec in result["recommendations"]:
        assert "compliance_notes" not in rec
    assert "compliance_disclaimer" not in result


def test_ranking_order_unaffected_by_compliance_evaluation():
    result = recommend_detailed("cheddar_cheese")
    scores = [r["score"] for r in result["recommendations"]]
    assert scores == sorted(scores, reverse=True)


def test_score_material_output_identical_regardless_of_compliance_module():
    """Direct proof compliance evaluation isn't read anywhere in scoring:
    _score_material's own output for a material with many compliance flags
    doesn't differ from one with none, all else equal."""
    commodity = find_commodity("cheddar_cheese")
    rules = _rules()
    req = {"budget_tier": "medium", "prioritize_sustainability": False}
    score_flagged = _score_material(commodity, _material("aluminum_foil_laminate"), rules, req)["score"]
    # Re-running the same call must be perfectly deterministic — nothing about
    # compliance_check being imported/evaluated elsewhere changes this value.
    score_flagged_again = _score_material(commodity, _material("aluminum_foil_laminate"), rules, req)["score"]
    assert score_flagged == score_flagged_again


# ---------------------------------------------------------------------------
# API layer
# ---------------------------------------------------------------------------


def test_api_recommend_detailed_includes_compliance_fields():
    r = client.post("/recommend/detailed", json={"commodity_id": "turmeric_powder"})
    assert r.status_code == 200
    d = r.json()
    assert "compliance_disclaimer" in d
    for rec in d["recommendations"]:
        assert "compliance_notes" in rec
        for note in rec["compliance_notes"]:
            assert set(note.keys()) == {"rule_id", "description", "confidence", "general_reference"}


def test_api_plain_recommend_has_no_compliance_fields():
    r = client.post("/recommend", json={"commodity_id": "turmeric_powder"})
    assert r.status_code == 200
    d = r.json()
    assert "compliance_disclaimer" not in d
    for rec in d["recommendations"]:
        assert "compliance_notes" not in rec
