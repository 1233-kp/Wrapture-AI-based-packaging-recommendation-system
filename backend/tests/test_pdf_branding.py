"""Tests for the Wrapture branding in PDF exports: the header logo next to
the title, and the large low-opacity watermark on every page. Distinct from
test_pdf_export.py, which covers report-content-consistency bugs — this file
is scoped purely to the logo/watermark rendering itself.
"""

import io
import uuid
from datetime import datetime, timezone

import pdfplumber

from engine.pdf_export import _LOGO_PATH, _WATERMARK_PATH, _WATERMARK_SIZE_PT, build_report_pdf
from engine.recommender import recommend_detailed


def _build_pdf_for(commodity_id: str, **kwargs) -> bytes:
    result = recommend_detailed(commodity_id, **kwargs)
    report = {
        "id": str(uuid.uuid4()),
        "commodity_name": result["commodity"]["name"],
        "input_conditions": kwargs,
        "recommendation": result,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return build_report_pdf(report)


def _page_images(pdf_bytes: bytes, page_index: int = 0) -> list[dict]:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return pdf.pages[page_index].images


# ---------------------------------------------------------------------------
# Assets themselves
# ---------------------------------------------------------------------------


def test_logo_and_watermark_assets_exist():
    assert _LOGO_PATH.exists()
    assert _WATERMARK_PATH.exists()


def test_watermark_asset_has_real_alpha_transparency():
    """Regression guard: this project has twice shipped a 'transparent' logo
    that turned out to be a flattened opaque image with the transparency
    baked in as visible pixels. Confirm the watermark asset genuinely has an
    alpha channel, not just a faint but fully-opaque background."""
    from PIL import Image

    img = Image.open(_WATERMARK_PATH)
    assert img.mode == "RGBA"
    alpha = img.getchannel("A")
    # A real transparent background should have plenty of near-zero-alpha
    # pixels (the surrounding transparent margin) and some non-zero-alpha
    # pixels (the faded mark itself) — not a single uniform value.
    extrema = alpha.getextrema()
    assert extrema[0] < extrema[1]


# ---------------------------------------------------------------------------
# Header logo
# ---------------------------------------------------------------------------


def test_header_logo_present_on_first_page():
    pdf_bytes = _build_pdf_for("banana")
    images = _page_images(pdf_bytes)
    # Small header-sized image (~11mm ≈ 31pt) distinct from the much larger
    # watermark and the QR code.
    assert any(25 < img["width"] < 40 for img in images), [img["width"] for img in images]


def test_header_logo_present_regardless_of_commodity():
    for commodity in ["banana", "chicken_fresh", "rice"]:
        pdf_bytes = _build_pdf_for(commodity)
        images = _page_images(pdf_bytes)
        assert any(25 < img["width"] < 40 for img in images), commodity


# ---------------------------------------------------------------------------
# Watermark: present on every page, doesn't break text
# ---------------------------------------------------------------------------


def test_watermark_present_on_first_page():
    pdf_bytes = _build_pdf_for("mango", ambient_temperature_c=25, expected_transport_days=3)
    images = _page_images(pdf_bytes, 0)
    widths = [img["width"] for img in images]
    assert any(w >= _WATERMARK_SIZE_PT - 1 for w in widths), widths


def test_watermark_present_on_every_page_of_a_multipage_report():
    """The actual bug report this feature was built for: a mango/premium
    report reliably spans 2+ pages — confirm the watermark isn't only on
    the first page."""
    pdf_bytes = _build_pdf_for(
        "mango", budget_tier="premium", ambient_temperature_c=25, expected_transport_days=3
    )
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        assert len(pdf.pages) >= 2, "expected a multi-page report for this scenario"
        for i, page in enumerate(pdf.pages):
            widths = [img["width"] for img in page.images]
            assert any(w >= _WATERMARK_SIZE_PT - 1 for w in widths), f"page {i + 1} missing watermark: {widths}"


def test_watermark_is_centered_on_the_page():
    from reportlab.lib.pagesizes import A4

    pdf_bytes = _build_pdf_for("banana")
    images = _page_images(pdf_bytes)
    watermark = next(img for img in images if img["width"] >= _WATERMARK_SIZE_PT - 1)
    page_w, page_h = A4
    expected_x0 = (page_w - _WATERMARK_SIZE_PT) / 2
    expected_top = (page_h - _WATERMARK_SIZE_PT) / 2
    assert abs(watermark["x0"] - expected_x0) < 1
    assert abs(watermark["top"] - expected_top) < 1


def test_watermark_does_not_corrupt_extracted_text():
    """The watermark is a background image, not text — confirm normal report
    text is still fully and correctly extractable with it present."""
    result = recommend_detailed("banana")
    pdf_bytes = _build_pdf_for("banana")
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    assert result["recommendations"][0]["material_name"] in text
    assert "Wrapture" in text


def test_missing_watermark_asset_does_not_break_pdf_generation(monkeypatch, tmp_path):
    """Defensive, same spirit as the header logo: a missing watermark file
    should degrade gracefully, never 500 the export endpoint."""
    import engine.pdf_export as pdf_export_module

    monkeypatch.setattr(pdf_export_module, "_WATERMARK_PATH", tmp_path / "does-not-exist.png")
    pdf_bytes = _build_pdf_for("banana")
    assert len(pdf_bytes) > 0
