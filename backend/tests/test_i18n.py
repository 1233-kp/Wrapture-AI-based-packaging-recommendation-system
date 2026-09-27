"""Tests for Hindi language support (engine/i18n_strings.py and its wiring
through recommend()/recommend_detailed()/build_agreement_note).

Uses a Devanagari-range check (U+0900-U+097F) as a genuine "is this actually
Hindi, not an English fallback" signal, rather than just checking the string
differs from the English version — a stray untranslated fragment could still
technically "differ" without being real Hindi.
"""

from fastapi.testclient import TestClient

from engine.recommender import _materials, find_commodity, recommend, recommend_detailed
from main import app

client = TestClient(app)

# Spans categories, including ones that exercise warnings/acidic-flag/high-fat paths.
SAMPLE_COMMODITY_IDS = ["banana", "strawberry", "chicken_fresh", "turmeric_powder", "cheddar_cheese", "dried_fish"]


def _has_devanagari(text: str) -> bool:
    return any("ऀ" <= ch <= "ॿ" for ch in text)


def _assert_all_devanagari(strings: list[str], context: str) -> None:
    for s in strings:
        assert _has_devanagari(s), f"{context}: expected Hindi text, got: {s!r}"


# ---------------------------------------------------------------------------
# recommend_detailed(lang="hi") — every dynamic text surface is genuinely Hindi
# ---------------------------------------------------------------------------


def test_recommend_detailed_hindi_rationale_and_warnings():
    for commodity_id in SAMPLE_COMMODITY_IDS:
        result = recommend_detailed(commodity_id, lang="hi", expected_transport_days=365)
        assert result is not None, commodity_id
        for rec in result["recommendations"]:
            _assert_all_devanagari(rec["rationale"], f"{commodity_id} rationale")
            _assert_all_devanagari(rec["warnings"], f"{commodity_id} warnings")
            assert _has_devanagari(rec["trade_off_summary"]), f"{commodity_id} trade_off_summary"
            if rec["cost_comparison_note"]:
                assert _has_devanagari(rec["cost_comparison_note"]), f"{commodity_id} cost_comparison_note"
            for item in rec["match_breakdown"]:
                assert _has_devanagari(item["explanation"]), f"{commodity_id} match_breakdown explanation"


def test_recommend_detailed_hindi_top_level_fields():
    result = recommend_detailed("strawberry", lang="hi")
    assert _has_devanagari(result["regulatory_note"])
    assert _has_devanagari(result["disclaimer"])
    assert _has_devanagari(result["map_gas_guidance"]["note"])
    assert result["ml_agreement"] is None or _has_devanagari(result["ml_agreement"]["note"])


def test_recommend_detailed_hindi_compliance_notes():
    """Compliance-flag descriptions and the compliance disclaimer must be genuinely
    Hindi in lang='hi' — general_reference deliberately stays English (regulatory
    body/framework proper nouns, not a sentence to translate)."""
    for commodity_id in ["turmeric_powder", "strawberry", "butter"]:
        result = recommend_detailed(commodity_id, lang="hi")
        any_notes = False
        for rec in result["recommendations"]:
            for note in rec["compliance_notes"]:
                any_notes = True
                assert _has_devanagari(note["description"]), f"{commodity_id}/{note['rule_id']} description"
                assert not _has_devanagari(note["general_reference"]), (
                    f"{commodity_id}/{note['rule_id']} general_reference should stay English"
                )
        if any_notes:
            assert _has_devanagari(result["compliance_disclaimer"])


def test_recommend_detailed_english_compliance_notes_unaffected():
    result = recommend_detailed("turmeric_powder", lang="en")
    for rec in result["recommendations"]:
        for note in rec["compliance_notes"]:
            assert not _has_devanagari(note["description"])


def test_recommend_detailed_hindi_non_respiring_commodity_map_gas_note():
    """Non-produce commodities get the 'not applicable' MAP note — must also be Hindi."""
    result = recommend_detailed("rice", lang="hi")
    assert result["map_gas_guidance"]["applicable"] is False
    assert _has_devanagari(result["map_gas_guidance"]["note"])


def test_recommend_hindi_disclaimer():
    result = recommend("banana", lang="hi")
    assert _has_devanagari(result["disclaimer"])


# ---------------------------------------------------------------------------
# English default — completely unaffected (no accidental Hindi leakage)
# ---------------------------------------------------------------------------


def test_recommend_detailed_default_lang_is_english():
    result = recommend_detailed("strawberry")
    for rec in result["recommendations"]:
        for s in rec["rationale"] + rec["warnings"]:
            assert not _has_devanagari(s)
    assert not _has_devanagari(result["regulatory_note"])
    assert not _has_devanagari(result["disclaimer"])


def test_recommend_detailed_lang_en_explicit_matches_default():
    default_result = recommend_detailed("banana")
    explicit_en_result = recommend_detailed("banana", lang="en")
    assert default_result["recommendations"][0]["rationale"] == explicit_en_result["recommendations"][0]["rationale"]
    assert default_result["disclaimer"] == explicit_en_result["disclaimer"]


def test_unsupported_lang_falls_back_to_english_not_a_crash():
    result = recommend_detailed("banana", lang="fr")
    assert result is not None
    assert not _has_devanagari(result["disclaimer"])


# ---------------------------------------------------------------------------
# display_name_hi data coverage
# ---------------------------------------------------------------------------


def test_every_commodity_has_a_hindi_display_name():
    from engine.recommender import list_commodities

    for commodity in list_commodities():
        name_hi = commodity.get("display_name_hi")
        assert name_hi, f"{commodity['id']} missing display_name_hi"
        assert _has_devanagari(name_hi), f"{commodity['id']}'s display_name_hi isn't Devanagari: {name_hi!r}"


def test_every_material_has_a_hindi_display_name():
    for material in _materials():
        name_hi = material.get("display_name_hi")
        assert name_hi, f"{material['id']} missing display_name_hi"
        assert _has_devanagari(name_hi), f"{material['id']}'s display_name_hi isn't Devanagari: {name_hi!r}"


def test_commodity_and_material_hindi_names_surfaced_in_recommend_detailed():
    result = recommend_detailed("strawberry", lang="hi")
    assert result["commodity"]["name_hi"] == find_commodity("strawberry")["display_name_hi"]
    for rec in result["recommendations"]:
        assert rec["material_name_hi"], rec["material_id"]


# ---------------------------------------------------------------------------
# API layer: lang field on the request body
# ---------------------------------------------------------------------------


def test_api_recommend_detailed_lang_hi():
    r = client.post("/recommend/detailed", json={"commodity_id": "banana", "lang": "hi"})
    assert r.status_code == 200
    d = r.json()
    assert _has_devanagari(d["disclaimer"])
    assert _has_devanagari(d["regulatory_note"])
    assert d["commodity"]["name_hi"]
    assert d["recommendations"][0]["material_name_hi"]


def test_api_recommend_lang_hi():
    r = client.post("/recommend", json={"commodity_id": "banana", "lang": "hi"})
    assert r.status_code == 200
    d = r.json()
    assert _has_devanagari(d["disclaimer"])
    assert d["commodity"]["name_hi"]


def test_api_recommend_detailed_default_lang_is_english():
    r = client.post("/recommend/detailed", json={"commodity_id": "banana"})
    assert r.status_code == 200
    d = r.json()
    assert not _has_devanagari(d["disclaimer"])


def test_api_commodities_list_includes_hindi_names():
    r = client.get("/commodities")
    assert r.status_code == 200
    d = r.json()
    assert all(c["name_hi"] for c in d["commodities"])


def test_api_commodities_search_includes_hindi_names():
    r = client.get("/commodities/search", params={"q": "banana"})
    assert r.status_code == 200
    d = r.json()
    assert len(d["commodities"]) >= 1
    assert d["commodities"][0]["name_hi"] == "केला"
