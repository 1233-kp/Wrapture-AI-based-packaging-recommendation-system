"""QR code generation for the report-verification feature.

Generated on-demand, not stored — a QR code encoding {FRONTEND_URL}/verify/{id}
is 100% deterministic from the report id, so there's nothing to persist or ever
go stale. Used by both GET /reports/{id}/qrcode (inline display right after
saving) and GET /reports/{id}/export (embedded in the PDF).
"""

import io

import qrcode

from core.config import get_settings


def build_verification_url(report_id: str) -> str:
    settings = get_settings()
    return f"{settings.frontend_url.rstrip('/')}/verify/{report_id}"


def generate_qr_png_bytes(report_id: str) -> bytes:
    url = build_verification_url(report_id)
    img = qrcode.make(url, box_size=8, border=2)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
