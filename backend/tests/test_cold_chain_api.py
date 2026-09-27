"""Tests for POST /reports/{id}/cold-chain-event and
GET /reports/{id}/cold-chain-events. Same isolated-app pattern as
test_delete_report.py/test_public_report.py: a minimal app with just the
reports router, Supabase calls monkeypatched.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.reports as reports_module
from api.reports import router as reports_router
from core.auth import CurrentUser, get_current_user
from engine.recommender import recommend_detailed

app = FastAPI()
app.include_router(reports_router)
client = TestClient(app)

FAKE_REPORT_ID = "33333333-3333-3333-3333-333333333333"
FAKE_OWNER_ID = "99999999-9999-9999-9999-333333333333"
FAKE_USER = CurrentUser(user_id=FAKE_OWNER_ID, email="owner@example.com", role="authenticated", access_token="fake-token")

FAKE_REPORT_ROW = {
    "id": FAKE_REPORT_ID,
    "user_id": FAKE_OWNER_ID,
    "commodity_name": "Banana",
    "input_conditions": {"ambient_temperature_c": 25},
    "recommendation": recommend_detailed("banana", ambient_temperature_c=25),
    "created_at": "2026-01-01T00:00:00+00:00",
}


def _with_auth_and_report(monkeypatch):
    monkeypatch.setattr(reports_module, "get_report", lambda access_token, report_id: FAKE_REPORT_ROW)
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER


def test_cold_chain_event_requires_auth():
    res = client.post(f"/reports/{FAKE_REPORT_ID}/cold-chain-event", json={"temperature_reached_c": 30, "duration_hours": 2})
    assert res.status_code == 401


def test_cold_chain_event_404s_for_someone_elses_or_missing_report(monkeypatch):
    monkeypatch.setattr(reports_module, "get_report", lambda access_token, report_id: None)
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    try:
        res = client.post(f"/reports/{FAKE_REPORT_ID}/cold-chain-event", json={"temperature_reached_c": 30, "duration_hours": 2})
    finally:
        app.dependency_overrides.clear()
    assert res.status_code == 404


def test_mild_excursion_returns_ok_action(monkeypatch):
    inserted = {}

    def fake_insert(access_token, row):
        inserted.update(row)
        return {**row, "id": "aaaaaaaa-1111-1111-1111-111111111111", "created_at": "2026-01-02T00:00:00+00:00"}

    _with_auth_and_report(monkeypatch)
    monkeypatch.setattr(reports_module, "insert_cold_chain_event", fake_insert)
    try:
        res = client.post(
            f"/reports/{FAKE_REPORT_ID}/cold-chain-event",
            json={"temperature_reached_c": 27, "duration_hours": 1},
        )
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 201
    data = res.json()
    assert data["event"]["action_urgent"] is False
    assert "no action needed" in data["action_message"].lower() or "urgent" not in data["action_message"].lower()
    # Confirms the event is scoped to the caller and the report, not trusted
    # from anywhere else in the request.
    assert inserted["user_id"] == FAKE_USER.user_id
    assert inserted["report_id"] == FAKE_REPORT_ID


def test_severe_excursion_returns_urgent_action(monkeypatch):
    def fake_insert(access_token, row):
        return {**row, "id": "aaaaaaaa-2222-2222-2222-222222222222", "created_at": "2026-01-02T00:00:00+00:00"}

    _with_auth_and_report(monkeypatch)
    monkeypatch.setattr(reports_module, "insert_cold_chain_event", fake_insert)
    try:
        res = client.post(
            f"/reports/{FAKE_REPORT_ID}/cold-chain-event",
            json={"temperature_reached_c": 40, "duration_hours": 48},
        )
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 201
    data = res.json()
    assert data["event"]["action_urgent"] is True


def test_cold_chain_event_creates_new_record_original_report_untouched(monkeypatch):
    """The endpoint should never call anything that mutates the reports
    table — only insert_cold_chain_event, a separate table."""
    calls = {"update_report_called": False}

    def fake_insert(access_token, row):
        return {**row, "id": "aaaaaaaa-3333-3333-3333-333333333333", "created_at": "2026-01-02T00:00:00+00:00"}

    def fake_update_report(*args, **kwargs):
        calls["update_report_called"] = True

    _with_auth_and_report(monkeypatch)
    monkeypatch.setattr(reports_module, "insert_cold_chain_event", fake_insert)
    monkeypatch.setattr(reports_module, "update_report", fake_update_report)
    try:
        client.post(
            f"/reports/{FAKE_REPORT_ID}/cold-chain-event",
            json={"temperature_reached_c": 40, "duration_hours": 48},
        )
    finally:
        app.dependency_overrides.clear()

    assert calls["update_report_called"] is False


def test_list_cold_chain_events(monkeypatch):
    fake_events = [
        {
            "id": "aaaaaaaa-1111-1111-1111-111111111111",
            "report_id": FAKE_REPORT_ID,
            "temperature_reached_c": 40,
            "duration_hours": 48,
            "remaining_shelf_life_days": 0.0,
            "action_urgent": True,
            "created_at": "2026-01-02T00:00:00+00:00",
        }
    ]
    monkeypatch.setattr(reports_module, "list_cold_chain_events", lambda access_token, report_id: fake_events)
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    try:
        res = client.get(f"/reports/{FAKE_REPORT_ID}/cold-chain-events")
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 200
    assert len(res.json()["events"]) == 1
    assert res.json()["events"][0]["action_urgent"] is True


def test_unrecognized_commodity_returns_422_not_a_fabricated_answer(monkeypatch):
    """If the report's commodity can't be resolved, the endpoint should say
    so explicitly rather than return a made-up shelf-life number."""
    broken_report = {**FAKE_REPORT_ROW, "recommendation": {"commodity": {"id": "not-a-real-commodity"}}}
    monkeypatch.setattr(reports_module, "get_report", lambda access_token, report_id: broken_report)
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    try:
        res = client.post(
            f"/reports/{FAKE_REPORT_ID}/cold-chain-event",
            json={"temperature_reached_c": 30, "duration_hours": 2},
        )
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 422
