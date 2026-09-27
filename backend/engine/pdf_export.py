"""Renders a saved report row into a PDF summary via reportlab.

reportlab was chosen over weasyprint specifically because it's pure-Python —
weasyprint needs system-level Cairo/Pango libraries that are painful to
install on Windows, which is where this project is being developed.

Defensive by design: `recommendation` and `input_conditions` are stored as
free-form JSONB, so nothing here assumes a field is present — a report saved
from an older client version should still render *something* useful instead
of throwing a 500. The expected shape is whatever POST /recommend/detailed
returns; see models/schemas.py's DetailedRecommendResponse for the full shape.
"""

import io
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from engine.qr_code import build_verification_url, generate_qr_png_bytes

# Own copy of the logo (not a reference into frontend/src/assets) so this
# backend keeps working if it's ever deployed separately from the frontend.
_LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "wrapture-mark.png"

# Same mark, pre-faded to ~8% opacity (baked into the alpha channel itself,
# not relying on reportlab's canvas alpha state for images) — large, centered
# background watermark on every page, in the same spirit as the landing page
# hero's watermark. Higher than the hero's 6%: verified by rendering actual
# output that the PDF pipeline (rasterize -> compress -> re-render) needs
# more than 6% to stay visibly perceptible on paper/screen, where 6% turned
# out imperceptible. A separate asset from _LOGO_PATH so the crisp header
# logo is never affected by this.
_WATERMARK_PATH = Path(__file__).resolve().parent.parent / "assets" / "wrapture-watermark.png"
_WATERMARK_SIZE_PT = 420

_styles = getSampleStyleSheet()
_title_style = ParagraphStyle("PSA_Title", parent=_styles["Title"], fontSize=18, spaceAfter=4)
_h2_style = ParagraphStyle("PSA_H2", parent=_styles["Heading2"], spaceBefore=14, spaceAfter=6)
_h3_style = ParagraphStyle("PSA_H3", parent=_styles["Heading3"], spaceBefore=10, spaceAfter=4)
_body_style = _styles["BodyText"]
_small_style = ParagraphStyle("PSA_Small", parent=_styles["BodyText"], fontSize=8, textColor=colors.grey)
_stat_style = ParagraphStyle("PSA_Stat", parent=_styles["BodyText"], fontName="Helvetica-Bold", spaceBefore=2)


def _fmt_range(range_dict: Any) -> str:
    if not isinstance(range_dict, dict) or "min" not in range_dict or "max" not in range_dict:
        return "n/a"
    return f"{range_dict['min']}-{range_dict['max']}"


def _draw_watermark(canvas, doc) -> None:
    """Large, centered, low-opacity background mark on every page — drawn via
    reportlab's page-callback mechanism, which fires before the page's own
    flowable content is drawn, so this genuinely sits BEHIND the text/tables,
    not on top of them. Silently does nothing if the asset is missing —
    same defensive-by-design spirit as the header logo."""
    if not _WATERMARK_PATH.exists():
        return
    page_w, page_h = A4
    x = (page_w - _WATERMARK_SIZE_PT) / 2
    y = (page_h - _WATERMARK_SIZE_PT) / 2
    canvas.saveState()
    canvas.drawImage(
        str(_WATERMARK_PATH), x, y, width=_WATERMARK_SIZE_PT, height=_WATERMARK_SIZE_PT, mask="auto"
    )
    canvas.restoreState()


def _fmt_cost(cost_dict: Any) -> str | None:
    """INR spelled out, not the '₹' glyph — the base Helvetica font reportlab uses
    here doesn't reliably include that character."""
    if not isinstance(cost_dict, dict) or "min" not in cost_dict or "max" not in cost_dict:
        return None
    return f"INR {cost_dict['min']:g}-{cost_dict['max']:g} per kg packaged (estimated)"


def build_report_pdf(report: dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Wrapture Report",
    )

    story: list[Any] = []

    commodity_name = report.get("commodity_name", "Unknown commodity")
    report_id = str(report.get("id", ""))
    created_at = report.get("created_at")

    title_paragraph = Paragraph("Wrapture — Packaging Recommendation Report", _title_style)
    if _LOGO_PATH.exists():
        # Real (square, 1:1) source image, so a single width/height pair here
        # can't distort it — no separate aspect-ratio bookkeeping needed.
        logo_image = Image(str(_LOGO_PATH), width=11 * mm, height=11 * mm)
        title_row = Table([[logo_image, title_paragraph]], colWidths=[14 * mm, None])
        title_row.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (0, 0), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        title_flowable = title_row
    else:
        # Defensive: a missing logo asset shouldn't break report export.
        title_flowable = title_paragraph

    header_text = [
        title_flowable,
        Paragraph(f"Commodity: <b>{commodity_name}</b>", _body_style),
        Paragraph(f"Report ID: {report_id or 'n/a'}", _small_style),
        Paragraph(f"Saved: {created_at or 'n/a'} · Generated: {datetime.utcnow().isoformat()}Z", _small_style),
    ]

    if report_id:
        # Same QR the /reports/{id}/qrcode endpoint serves — generated on-demand here
        # too rather than stored, since it's fully deterministic from the report id.
        qr_png = generate_qr_png_bytes(report_id)
        qr_image = Image(io.BytesIO(qr_png), width=26 * mm, height=26 * mm)
        qr_cell = [
            qr_image,
            Paragraph("Scan to verify this recommendation.", _small_style),
        ]
        header_table = Table([[header_text, qr_cell]], colWidths=[128 * mm, 34 * mm])
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (1, 0), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(header_table)
    else:
        story.extend(header_text)

    story.append(Spacer(1, 8))

    # -- input conditions --
    conditions = report.get("input_conditions") or {}
    if conditions:
        story.append(Paragraph("Requested Conditions", _h2_style))
        rows = [[str(k).replace("_", " ").title(), str(v)] for k, v in conditions.items()]
        table = Table(rows, colWidths=[60 * mm, 100 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(table)

    recommendation = report.get("recommendation") or {}
    recommendations = recommendation.get("recommendations") or []

    if not recommendations:
        story.append(Spacer(1, 8))
        story.append(Paragraph("No recommendation data was stored with this report.", _body_style))
        doc.build(story, onFirstPage=_draw_watermark, onLaterPages=_draw_watermark)
        return buffer.getvalue()

    top = recommendations[0]
    alternatives = recommendations[1:]

    # -- top recommendation --
    story.append(Paragraph("Top Recommendation", _h2_style))
    story.append(
        Paragraph(
            f"<b>{top.get('material_name', top.get('material_id', 'Unknown material'))}</b> "
            f"— fit score {top.get('score', 'n/a')}/100, sustainability {top.get('sustainability_score', 'n/a')}/100",
            _body_style,
        )
    )
    confidence = top.get("overall_confidence")
    if confidence in ("low", "medium"):
        story.append(Paragraph(f"<i>Estimated — underlying data confidence: {confidence}.</i>", _small_style))
    story.append(Paragraph(f"Cost tier: {top.get('cost_tier', 'n/a')}", _body_style))
    top_cost_text = _fmt_cost(top.get("estimated_cost_per_unit_inr"))
    if top_cost_text:
        story.append(Paragraph(f"Estimated cost: {top_cost_text}", _body_style))
    story.append(Paragraph(f"Recyclability: {top.get('recyclability_rating', 'n/a')}", _body_style))
    if top.get("trade_off_summary"):
        story.append(Paragraph(f"Trade-off: {top['trade_off_summary']}", _body_style))
    if top.get("ml_confidence_score") is not None:
        story.append(
            Paragraph(f"ML model confidence: {top['ml_confidence_score']:.0f}/100", _stat_style)
        )

    rationale = top.get("rationale") or []
    if rationale:
        story.append(Paragraph("Why this material:", _h3_style))
        story.append(ListFlowable([ListItem(Paragraph(r, _body_style)) for r in rationale], bulletType="bullet"))

    warnings = top.get("warnings") or []
    if warnings:
        story.append(Paragraph("Warnings:", _h3_style))
        warn_style = ParagraphStyle("PSA_Warn", parent=_body_style, textColor=colors.HexColor("#b00020"))
        story.append(ListFlowable([ListItem(Paragraph(w, warn_style)) for w in warnings], bulletType="bullet"))

    match_breakdown = top.get("match_breakdown") or []
    if match_breakdown:
        story.append(Paragraph("Scoring Breakdown:", _h3_style))
        cell_style = ParagraphStyle("PSA_Cell", parent=_body_style, fontSize=7.5, leading=9)
        header_style = ParagraphStyle("PSA_CellHeader", parent=cell_style, fontName="Helvetica-Bold")
        header = [Paragraph(h, header_style) for h in ["Dimension", "Commodity Property", "Packaging Property", "Fit"]]
        rows = [header]
        for item in match_breakdown:
            rows.append(
                [
                    Paragraph(str(item.get("dimension", "")).replace("_", " "), cell_style),
                    Paragraph(str(item.get("commodity_property", "")), cell_style),
                    Paragraph(str(item.get("packaging_property", "")), cell_style),
                    Paragraph(str(item.get("fit", "")), cell_style),
                ]
            )
        # Cell content is wrapped in Paragraph (not plain strings) so reportlab word-wraps
        # within these fixed widths instead of letting long text overflow into neighboring cells.
        table = Table(rows, colWidths=[24 * mm, 52 * mm, 52 * mm, 20 * mm], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(table)

    # -- ML model cross-check --
    # Corroborating signal only, from the supervised model in /backend/training —
    # never the ranking driver. See DetailedRecommendResponse.ml_agreement.
    ml_agreement = recommendation.get("ml_agreement")
    if isinstance(ml_agreement, dict) and ml_agreement.get("note"):
        story.append(Paragraph("ML Model Cross-Check", _h3_style))
        tone_prefix = "✓" if ml_agreement.get("agrees") else "⚠"
        story.append(Paragraph(f"{tone_prefix} {ml_agreement['note']}", _small_style))

    # -- temperature-adjusted shelf-life prediction (Q10 method) --
    # Material-independent — a single commodity-level fact, not per-option. See
    # DetailedRecommendResponse.shelf_life_prediction / data/shelf_life_rules.json.
    shelf_life_prediction = recommendation.get("shelf_life_prediction")
    if isinstance(shelf_life_prediction, dict):
        story.append(Paragraph("Temperature-Adjusted Shelf Life", _h3_style))
        story.append(
            Paragraph(
                f"Predicted: {shelf_life_prediction.get('predicted_shelf_life_days', 'n/a')} days "
                f"<i>(confidence: {shelf_life_prediction.get('shelf_life_confidence', 'n/a')})</i>",
                _body_style,
            )
        )
        story.append(Paragraph(shelf_life_prediction.get("explanation", ""), _small_style))
        story.append(Paragraph(shelf_life_prediction.get("disclaimer", ""), _small_style))

    # -- regulatory considerations (compliance flags) --
    # Informational only, from the small rule set in data/compliance_rules.json —
    # never a certified compliance check. See DetailedMaterialRecommendation.compliance_notes.
    compliance_notes = top.get("compliance_notes") or []
    if compliance_notes:
        story.append(Paragraph("Regulatory Considerations", _h3_style))
        note_style = ParagraphStyle("PSA_ComplianceNote", parent=_small_style, textColor=colors.black)
        ref_style = ParagraphStyle("PSA_ComplianceRef", parent=_small_style, fontSize=7)
        for note in compliance_notes:
            confidence = note.get("confidence", "")
            story.append(
                Paragraph(
                    f"• <b>[{confidence}]</b> {note.get('description', '')}",
                    note_style,
                )
            )
            story.append(Paragraph(f"   Ref: {note.get('general_reference', '')}", ref_style))
        compliance_disclaimer = recommendation.get("compliance_disclaimer")
        if compliance_disclaimer:
            story.append(Spacer(1, 3))
            story.append(Paragraph(compliance_disclaimer, ref_style))

    # -- government scheme linkage --
    # Distinct from Regulatory Considerations above: an informational note that
    # packaging equipment upgrades may be eligible for PM-FME scheme support —
    # always present, not triggered by any rule, and never a claim that this
    # specific recommendation is confirmed eligible. See engine/government_scheme.py.
    government_scheme_note = recommendation.get("government_scheme_note")
    if government_scheme_note:
        story.append(Paragraph("Government Scheme Linkage", _h3_style))
        story.append(Paragraph(government_scheme_note, _small_style))

    # -- alternatives --
    if alternatives:
        story.append(Paragraph("Alternatives", _h2_style))
        for alt in alternatives:
            story.append(
                Paragraph(
                    f"<b>{alt.get('material_name', alt.get('material_id', 'Unknown'))}</b> "
                    f"— score {alt.get('score', 'n/a')}/100, sustainability {alt.get('sustainability_score', 'n/a')}/100",
                    _body_style,
                )
            )
            if alt.get("trade_off_summary"):
                story.append(Paragraph(alt["trade_off_summary"], _small_style))
            alt_cost_text = _fmt_cost(alt.get("estimated_cost_per_unit_inr"))
            if alt_cost_text:
                cost_line = f"Estimated cost: {alt_cost_text}"
                if alt.get("cost_comparison_note"):
                    cost_line += f" — {alt['cost_comparison_note']}"
                story.append(Paragraph(cost_line, _small_style))
            alt_compliance_notes = alt.get("compliance_notes") or []
            if alt_compliance_notes:
                count = len(alt_compliance_notes)
                plural = "s" if count != 1 else ""
                # The "Regulatory Considerations" section above only ever prints the TOP
                # pick's own notes, never each alternative's — pointing the reader "above"
                # for an alternative whose notes actually differ (or when the top pick had
                # none at all, so there's no section above to point to) would be a false
                # claim. Only say "see above" when the alternative's own rule set is
                # genuinely identical to what's actually printed there.
                alt_rule_ids = {n.get("rule_id") for n in alt_compliance_notes}
                top_rule_ids = {n.get("rule_id") for n in compliance_notes}
                verb = "apply" if count != 1 else "applies"
                if compliance_notes and alt_rule_ids == top_rule_ids:
                    text = (
                        f"⚠ {count} regulatory consideration{plural} — same categories as shown in "
                        "Regulatory Considerations above."
                    )
                else:
                    text = f"⚠ {count} regulatory consideration{plural} {verb} to this material."
                story.append(Paragraph(text, _small_style))
            story.append(Spacer(1, 4))

    # -- MAP gas guidance --
    map_guidance = recommendation.get("map_gas_guidance")
    if isinstance(map_guidance, dict) and map_guidance.get("applicable"):
        story.append(Paragraph("General MAP Gas Guidance", _h2_style))
        story.append(
            Paragraph(
                f"Respiration class: {map_guidance.get('respiration_rate_class', 'n/a')} — "
                f"O2 {_fmt_range(map_guidance.get('o2_percent'))}%, "
                f"CO2 {_fmt_range(map_guidance.get('co2_percent'))}%, "
                f"N2 {_fmt_range(map_guidance.get('n2_percent'))}%",
                _body_style,
            )
        )
        note = map_guidance.get("note")
        if note:
            story.append(Paragraph(note, _small_style))

    story.append(Spacer(1, 12))
    disclaimer = recommendation.get("disclaimer") or (
        "Generated from heuristic rules and typical literature ranges, not lab testing. "
        "Validate before production use."
    )
    story.append(Paragraph(disclaimer, _small_style))

    doc.build(story, onFirstPage=_draw_watermark, onLaterPages=_draw_watermark)
    return buffer.getvalue()
