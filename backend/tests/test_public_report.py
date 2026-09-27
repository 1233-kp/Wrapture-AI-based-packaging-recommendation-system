"""Tests for the public, no-auth report-verification endpoints (QR traceability).

Uses a minimal standalone app with just the reports router — not the full
main.app — so these tests don't pay the sentence-transformers model-load cost
from the commodity-matcher startup event, and don't need real Supabase
network access: get_report_service_role is monkeypatched per test.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.reports as reports_module
from api.reports import router as reports_router
from engine.qr_code import build_verification_url
from engine.recommender import recommend_detailed

app = FastAPI()
app.include_router(reports_router)
client = TestClient(app)

FAKE_REPORT_ID = "11111111-1111-1111-1111-111111111111"
FAKE_OWNER_ID = "99999999-9999-9999-9999-999999999999"
FAKE_OWNER_EMAIL = "owner-should-never-appear@example.com"

FAKE_ROW = {
    "id": FAKE_REPORT_ID,
    "user_id": FAKE_OWNER_ID,
    "email": FAKE_OWNER_EMAIL,  # not a real reports-table column, but proves it wouldn't leak even if present
    "commodity_name": "Banana",
    "input_conditions": {"budget_tier": "standard"},
    "recommendation": recommend_detailed("banana"),
    "created_at": "2026-01-01T00:00:00+00:00",
}


def test_public_endpoint_returns_limited_fields(monkeypatch):
    monkeypatch.setattr(reports_module, "get_report_service_role", lambda report_id: FAKE_ROW)

    res = client.get(f"/reports/{FAKE_REPORT_ID}/public")

    assert res.status_code == 200
    data = res.json()
    assert set(data.keys()) == {
        "trace_id",
        "commodity_name",
        "material_name",
        "otr_cm3_m2_day_atm",
        "wvtr_g_m2_day",
        "thickness_range_micron",
        "sustainability_score",
        "generated_at",
    }
    assert data["commodity_name"] == "Banana"
    assert data["trace_id"].startswith("PSA-")
    assert data["material_name"]  # the top recommendation's material, non-empty


def test_public_endpoint_404_for_nonexistent_report(monkeypatch):
    monkeypatch.setattr(reports_module, "get_report_service_role", lambda report_id: None)

    res = client.get("/reports/does-not-exist/public")

    assert res.status_code == 404


def test_public_endpoint_never_leaks_owner_information(monkeypatch):
    """The strongest version of this check: search the raw HTTP response body
    text for the owner's id/email, not just assert on parsed keys — this would
    catch a leak even if it snuck in through an unexpected field."""
    monkeypatch.setattr(reports_module, "get_report_service_role", lambda report_id: FAKE_ROW)

    res = client.get(f"/reports/{FAKE_REPORT_ID}/public")

    body_text = res.text
    assert FAKE_OWNER_ID not in body_text
    assert FAKE_OWNER_EMAIL not in body_text
    assert "user_id" not in body_text
    assert "email" not in body_text.lower()


def test_qrcode_endpoint_returns_png_for_valid_report(monkeypatch):
    monkeypatch.setattr(reports_module, "get_report_service_role", lambda report_id: FAKE_ROW)

    res = client.get(f"/reports/{FAKE_REPORT_ID}/qrcode")

    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    assert res.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_qrcode_endpoint_404_for_nonexistent_report(monkeypatch):
    monkeypatch.setattr(reports_module, "get_report_service_role", lambda report_id: None)

    res = client.get("/reports/does-not-exist/qrcode")

    assert res.status_code == 404


def test_qr_encodes_the_public_verify_url():
    url = build_verification_url(FAKE_REPORT_ID)
    assert url.endswith(f"/verify/{FAKE_REPORT_ID}")


def test_existing_protected_reports_endpoints_still_require_auth():
    """Sanity check that adding the public endpoints didn't loosen anything on
    the existing protected ones — no auth header should still be rejected."""
    assert client.get("/reports").status_code == 401
    assert client.post("/reports", json={}).status_code == 401
    assert client.get(f"/reports/{FAKE_REPORT_ID}/export").status_code == 401
