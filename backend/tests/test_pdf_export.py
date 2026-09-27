"""Regression tests for two report-consistency bugs found in a generated PDF
(mango, premium/sustainability-priority case):

1. Alternatives claimed "see Regulatory Considerations above for this
   pairing's details" even when the Regulatory Considerations section only
   ever prints the TOP pick's own notes — a false pointer whenever an
   alternative's notes differ from (or the top pick has none while an
   alternative does).

2. The Scoring Breakdown's cost row displayed "Requested budget tier: High"
   when the actual requested value was "premium" — the internal low/medium/
   high mapping was shown silently as if it were the literal request.

Both are checked at two levels: the underlying data (recommend_detailed's
match_breakdown / compliance_notes) and the actual rendered PDF text (via
pdfplumber), since the second bug specifically was about what gets PRINTED,
not just what data is available.
"""

import uuid
from datetime import datetime, timezone

import pdfplumber

from engine.pdf_export import build_report_pdf
from engine.recommender import recommend_detailed


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    import io

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


# ---------------------------------------------------------------------------
# Bug 1: alternatives' compliance-notes referral text
# ---------------------------------------------------------------------------


def test_alternative_referral_text_never_falsely_points_above_when_notes_differ():
    """The exact reported scenario: mango, premium budget + sustainability
    priority. Confirms every alternative whose notes differ from the top
    pick's does NOT claim 'see ... above', and instead states only the count."""
    result = recommend_detailed("mango", budget_tier="premium", prioritize_sustainability=True)
    top = result["recommendations"][0]
    alternatives = result["recommendations"][1:]
    assert len(alternatives) >= 1, "test needs at least one alternative to be meaningful"

    top_rule_ids = {n["rule_id"] for n in top["compliance_notes"]}

    pdf_text = _extract_pdf_text(_build_pdf_for(result))

    for alt in alternatives:
        alt_rule_ids = {n["rule_id"] for n in alt["compliance_notes"]}
        if not alt["compliance_notes"]:
            continue  # nothing to claim either way
        count = len(alt["compliance_notes"])
        if alt_rule_ids == top_rule_ids and top["compliance_notes"]:
            # Genuinely the same set as what's printed above — the "above" claim is true.
            assert "same categories as shown in Regulatory Considerations above" in pdf_text
        else:
            # Different set (or top pick had none) — must NOT claim detail exists above.
            assert f"{count} regulatory consideration" in pdf_text
            # The false claim from the original bug, scoped to this specific count, must
            # not appear — a different alternative's own true "same categories" line
            # (if any) elsewhere in the PDF doesn't make this assertion vacuous, since
            # we're checking there's no "above" claim attached to THIS mismatched count.
            assert f"{count} regulatory considerations — same categories" not in pdf_text or alt_rule_ids == top_rule_ids


def test_alternative_referral_text_matches_when_notes_genuinely_identical():
    """Positive case: turmeric_powder's top two options (metalized_film,
    aluminum_foil_laminate) are both flexible_film_laminate materials that
    trigger the identical 4-rule set — confirms the 'same categories above'
    text is used correctly when it's actually true, not just suppressed."""
    result = recommend_detailed("turmeric_powder")
    recommendations = result["recommendations"]
    top = recommendations[0]
    assert top["compliance_notes"], "test assumes the top pick has notes"

    top_rule_ids = {n["rule_id"] for n in top["compliance_notes"]}
    matching_alt = next(
        (r for r in recommendations[1:] if {n["rule_id"] for n in r["compliance_notes"]} == top_rule_ids),
        None,
    )
    assert matching_alt is not None, "test assumes at least one alternative shares the top pick's exact rule set"

    pdf_text = _extract_pdf_text(_build_pdf_for(result))
    assert "same categories as shown in Regulatory Considerations above" in pdf_text


def test_pdf_never_contains_the_original_unconditional_false_claim():
    """The exact string from the original bug — unconditionally pointing
    'above' regardless of whether the notes actually match — must never
    appear verbatim again."""
    result = recommend_detailed("mango", budget_tier="premium", prioritize_sustainability=True)
    pdf_text = _extract_pdf_text(_build_pdf_for(result))
    assert "see Regulatory Considerations above for this pairing's details" not in pdf_text


# ---------------------------------------------------------------------------
# Bug 2: cost row's requested-budget-tier label
# ---------------------------------------------------------------------------


def test_cost_row_shows_the_literal_requested_tier_not_just_the_internal_mapping():
    """Requesting 'premium' must show 'Premium' somewhere in the cost row's
    commodity_property text, not just 'High' (the internal cost-tolerance
    tier premium maps to for scoring) standing in for it unexplained."""
    result = recommend_detailed("mango", budget_tier="premium")
    cost_row = next(c for c in result["recommendations"][0]["match_breakdown"] if c["dimension"] == "cost")
    assert "Premium" in cost_row["commodity_property"]
    # The internal mapping is still shown, but visibly labeled, not standing in unexplained.
    assert "high" in cost_row["commodity_property"].lower()


def test_cost_row_traceable_for_every_detailed_budget_tier():
    expected_labels = {"economy": "Economy", "standard": "Standard", "premium": "Premium"}
    expected_tolerance = {"economy": "low", "standard": "medium", "premium": "high"}
    for tier, expected_label in expected_labels.items():
        result = recommend_detailed("mango", budget_tier=tier)
        cost_row = next(c for c in result["recommendations"][0]["match_breakdown"] if c["dimension"] == "cost")
        text = cost_row["commodity_property"]
        assert expected_label in text, f"{tier}: expected {expected_label!r} in {text!r}"
        assert expected_tolerance[tier] in text.lower(), f"{tier}: expected tolerance word in {text!r}"


def test_cost_row_pdf_text_shows_requested_tier_not_bare_internal_word():
    """Reproduces the exact originally-reported symptom at the PDF text
    level: 'Requested budget tier: High' with no trace of 'premium' must
    never appear again."""
    result = recommend_detailed("mango", budget_tier="premium")
    pdf_text = _extract_pdf_text(_build_pdf_for(result))
    assert "Requested budget tier: Premium" in pdf_text
    assert "Requested budget tier: High" not in pdf_text


def test_plain_recommend_low_medium_high_vocabulary_still_displays_correctly():
    """The plain low/medium/high vocabulary (used directly by _score_material
    when called outside of recommend_detailed's economy/standard/premium
    mapping) must still display as-is — this fix must not affect that path."""
    from engine.recommender import _materials, _rules, _score_material, find_commodity

    commodity = find_commodity("mango")
    rules = _rules()
    material = next(m for m in _materials() if m["id"] == "hdpe")
    result = _score_material(commodity, material, rules, {"budget_tier": "high"})
    cost_row = next(c for c in result["components"] if c["dimension"] == "cost")
    assert cost_row["commodity_property"] == "Requested budget tier: High"
