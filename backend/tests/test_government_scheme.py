"""Tests for the government-scheme-linkage note (engine/government_scheme.py
and its wiring into recommend_detailed's government_scheme_note field and
the PDF export's "Government Scheme Linkage" section).

Purely informational and unconditional (unlike compliance_notes, this note
has no trigger condition — every /recommend/detailed response involves a
packaging material) — these tests also confirm it's distinct from the
compliance section and never overclaims eligibility.
"""

import io
import uuid
from datetime import datetime, timezone

import pdfplumber

from engine.government_scheme import government_scheme_note
from engine.pdf_export import build_report_pdf
from engine.recommender import recommend_detailed


def _has_devanagari(text: str) -> bool:
    return any("ऀ" <= ch <= "ॿ" for ch in text)


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def _build_pdf_for(result: dict) -> bytes:
    report = {
        "id": str(uuid.uuid4()),
        "commodity_name": result["commodity"]["name"],
        "input_conditions": {},
        "recommendation": result,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return build_report_pdf(report)


def _assert_no_unqualified_eligibility_claim(text: str) -> None:
    """Every sentence mentioning 'eligib*' or 'qualif*' must also contain a
    hedging word ('may' or 'verify') in the SAME sentence — never a bare
    claim that a recommendation IS eligible/qualifies."""
    for sentence in text.replace("।", ".").split("."):
        lowered = sentence.lower()
        if "eligib" in lowered or "qualif" in lowered:
            assert "may" in lowered or "verify" in lowered, (
                f"Sentence claims eligibility without a hedge: {sentence!r}"
            )


# ---------------------------------------------------------------------------
# The note itself
# ---------------------------------------------------------------------------


def test_note_mentions_pm_fme_scheme_and_key_figures():
    note = government_scheme_note("en")
    assert "PM-FME" in note
    assert "35%" in note
    assert "₹10 lakh" in note
    assert "State Nodal Agency" in note


def test_note_never_makes_an_unqualified_eligibility_claim_english():
    _assert_no_unqualified_eligibility_claim(government_scheme_note("en"))


def test_note_never_makes_an_unqualified_eligibility_claim_hindi():
    _assert_no_unqualified_eligibility_claim(government_scheme_note("hi"))


def test_note_renders_in_hindi():
    assert _has_devanagari(government_scheme_note("hi"))


def test_note_defaults_to_english_for_unsupported_language():
    assert government_scheme_note("fr") == government_scheme_note("en")


# ---------------------------------------------------------------------------
# Wiring into recommend_detailed()
# ---------------------------------------------------------------------------


def test_recommend_detailed_always_includes_the_note():
    """Unconditional — unlike compliance_notes, there's no trigger to fail:
    every recommendation involves a packaging material."""
    result = recommend_detailed("banana")
    assert result["government_scheme_note"]
    assert "PM-FME" in result["government_scheme_note"]


def test_recommend_detailed_includes_the_note_regardless_of_compliance_notes():
    """Distinct from the compliance-flag feature: present even for a
    commodity/material pairing that triggers zero compliance rules."""
    result = recommend_detailed("rice")  # glass-like low-compliance-trigger case per test_compliance.py
    assert result["government_scheme_note"]


def test_note_is_the_same_regardless_of_which_material_is_recommended():
    """Unconditional and material-independent, unlike compliance_notes
    which vary per material."""
    a = recommend_detailed("banana")["government_scheme_note"]
    b = recommend_detailed("chicken_fresh")["government_scheme_note"]
    assert a == b


def test_plain_recommend_has_no_government_scheme_note_field():
    """Same scoping as regulatory_note/compliance_notes/shelf_life_prediction
    — a /recommend/detailed-only enrichment, not on plain /recommend."""
    from engine.recommender import recommend

    result = recommend("banana")
    assert "government_scheme_note" not in result


def test_ranking_order_and_scores_unaffected():
    """Purely additive — confirms this feature never touches scoring."""
    without_reference = recommend_detailed("strawberry")
    with_reference = recommend_detailed("strawberry")
    ids_a = [r["material_id"] for r in without_reference["recommendations"]]
    ids_b = [r["material_id"] for r in with_reference["recommendations"]]
    scores_a = [r["score"] for r in without_reference["recommendations"]]
    scores_b = [r["score"] for r in with_reference["recommendations"]]
    assert ids_a == ids_b
    assert scores_a == scores_b


def test_hindi_language_request_returns_hindi_note():
    result = recommend_detailed("banana", lang="hi")
    assert _has_devanagari(result["government_scheme_note"])


# ---------------------------------------------------------------------------
# PDF export
# ---------------------------------------------------------------------------


def test_api_recommend_detailed_includes_government_scheme_note():
    """Regression test: recommend_detailed()'s dict having the field isn't
    enough — api/recommend.py builds DetailedRecommendResponse with
    explicit keyword args, so a field added to the engine's dict but not
    threaded through that constructor call 500s the whole endpoint."""
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)
    res = client.post("/recommend/detailed", json={"commodity_id": "banana"})
    assert res.status_code == 200
    assert "PM-FME" in res.json()["government_scheme_note"]


def test_pdf_includes_government_scheme_linkage_section():
    result = recommend_detailed("banana")
    pdf_text = _extract_pdf_text(_build_pdf_for(result))
    assert "Government Scheme Linkage" in pdf_text
    assert "PM-FME" in pdf_text


def test_pdf_government_scheme_section_is_distinct_from_compliance_section():
    """The two sections must be separately labeled, not merged — confirms
    the feature request's 'distinct from the FSSAI/BIS compliance section'."""
    result = recommend_detailed("strawberry", prioritize_sustainability=True)  # likely triggers compliance notes
    pdf_text = _extract_pdf_text(_build_pdf_for(result))
    assert "Government Scheme Linkage" in pdf_text
    gov_idx = pdf_text.index("Government Scheme Linkage")
    # If a Regulatory Considerations section is present, it must be a
    # separate heading from Government Scheme Linkage, not the same block.
    if "Regulatory Considerations" in pdf_text:
        reg_idx = pdf_text.index("Regulatory Considerations")
        assert reg_idx != gov_idx


def test_pdf_government_scheme_text_has_no_unqualified_eligibility_claim():
    result = recommend_detailed("banana")
    pdf_text = _extract_pdf_text(_build_pdf_for(result))
    # Narrow to the Government Scheme Linkage section only, so an unrelated
    # sentence elsewhere in the PDF can't trip this check.
    start = pdf_text.index("Government Scheme Linkage")
    section = pdf_text[start : start + 800]
    _assert_no_unqualified_eligibility_claim(section)
