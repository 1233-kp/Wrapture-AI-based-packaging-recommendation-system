"""Tests for DELETE /reports/{id} — user-initiated history cleanup, added
because auto-save (no more manual "Save" click) means users need a way to
remove entries they don't want kept.

Same isolated-app pattern as test_public_report.py: a minimal app with just
the reports router, so these don't need real Supabase credentials or the
sentence-transformers startup cost.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.reports as reports_module
from api.reports import router as reports_router
from core.auth import CurrentUser, get_current_user

app = FastAPI()
app.include_router(reports_router)
client = TestClient(app)

FAKE_REPORT_ID = "22222222-2222-2222-2222-222222222222"
FAKE_USER = CurrentUser(user_id="owner-id", email="owner@example.com", role="authenticated", access_token="fake-token")


def test_delete_requires_auth():
    """No dependency override here — the real get_current_user should reject
    a request with no bearer token before ever reaching delete_report_row."""
    res = client.delete(f"/reports/{FAKE_REPORT_ID}")
    assert res.status_code == 401


def test_delete_calls_supabase_scoped_to_caller_token_and_returns_204(monkeypatch):
    calls = []
    monkeypatch.setattr(
        reports_module,
        "delete_report_row",
        lambda access_token, report_id: calls.append((access_token, report_id)),
    )
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    try:
        res = client.delete(f"/reports/{FAKE_REPORT_ID}")
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 204
    # Confirms the delete is scoped by the caller's own token (which is what
    # makes the reports_delete_own RLS policy the actual enforcement point —
    # this endpoint never passes a user_id filter itself, RLS does that).
    assert calls == [(FAKE_USER.access_token, FAKE_REPORT_ID)]


def test_delete_of_someone_elses_report_is_a_silent_noop(monkeypatch):
    """RLS makes a mismatched-owner delete match zero rows rather than error —
    PostgREST returns success either way, so this endpoint can't and doesn't
    try to distinguish "deleted" from "wasn't yours", by design (see
    delete_report_row's docstring). We simulate that here: the mock simply
    doesn't raise, matching what RLS-filtered-to-zero-rows actually returns."""
    monkeypatch.setattr(reports_module, "delete_report_row", lambda access_token, report_id: None)
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    try:
        res = client.delete("/reports/someone-elses-report-id")
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 204
