"""Tests for PATCH /reports/{id}/feedback — pure data capture, no
retraining/auto-improvement logic anywhere downstream of this endpoint.
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

FAKE_REPORT_ID = "44444444-4444-4444-4444-444444444444"
FAKE_OWNER_ID = "99999999-9999-9999-9999-444444444444"
FAKE_USER = CurrentUser(user_id=FAKE_OWNER_ID, email="owner@example.com", role="authenticated", access_token="fake-token")

FAKE_REPORT_ROW = {
    "id": FAKE_REPORT_ID,
    "user_id": FAKE_OWNER_ID,
    "commodity_name": "Banana",
    "input_conditions": {},
    "recommendation": recommend_detailed("banana"),
    "created_at": "2026-01-01T00:00:00+00:00",
    "feedback_outcome": None,
    "feedback_submitted_at": None,
}


def test_feedback_requires_auth():
    res = client.patch(f"/reports/{FAKE_REPORT_ID}/feedback", json={"outcome": "as_expected"})
    assert res.status_code == 401


def test_submitting_feedback_updates_the_report(monkeypatch):
    captured = {}

    def fake_update_report(access_token, report_id, patch):
        captured["access_token"] = access_token
        captured["report_id"] = report_id
        captured["patch"] = patch
        return {**FAKE_REPORT_ROW, **patch}

    monkeypatch.setattr(reports_module, "update_report", fake_update_report)
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    try:
        res = client.patch(f"/reports/{FAKE_REPORT_ID}/feedback", json={"outcome": "spoiled_early"})
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 200
    data = res.json()
    assert data["feedback_outcome"] == "spoiled_early"
    assert data["feedback_submitted_at"] is not None
    # Scoped to the caller's own token, same as every other report mutation.
    assert captured["access_token"] == FAKE_USER.access_token
    assert captured["report_id"] == FAKE_REPORT_ID
    assert captured["patch"]["feedback_outcome"] == "spoiled_early"


def test_feedback_accepts_all_three_outcomes(monkeypatch):
    monkeypatch.setattr(
        reports_module, "update_report", lambda access_token, report_id, patch: {**FAKE_REPORT_ROW, **patch}
    )
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    try:
        for outcome in ["spoiled_early", "as_expected", "lasted_longer"]:
            res = client.patch(f"/reports/{FAKE_REPORT_ID}/feedback", json={"outcome": outcome})
            assert res.status_code == 200
            assert res.json()["feedback_outcome"] == outcome
    finally:
        app.dependency_overrides.clear()


def test_feedback_rejects_invalid_outcome(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    try:
        res = client.patch(f"/reports/{FAKE_REPORT_ID}/feedback", json={"outcome": "not_a_real_outcome"})
    finally:
        app.dependency_overrides.clear()
    assert res.status_code == 422


def test_feedback_404s_for_someone_elses_or_missing_report(monkeypatch):
    monkeypatch.setattr(reports_module, "update_report", lambda access_token, report_id, patch: None)
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    try:
        res = client.patch(f"/reports/{FAKE_REPORT_ID}/feedback", json={"outcome": "as_expected"})
    finally:
        app.dependency_overrides.clear()
    assert res.status_code == 404


def test_feedback_never_touches_recommendation_or_input_conditions(monkeypatch):
    """Confirms the patch sent to Supabase only ever contains the two
    feedback columns — never touches the original recommendation data."""
    captured = {}

    def fake_update_report(access_token, report_id, patch):
        captured["patch"] = patch
        return {**FAKE_REPORT_ROW, **patch}

    monkeypatch.setattr(reports_module, "update_report", fake_update_report)
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    try:
        client.patch(f"/reports/{FAKE_REPORT_ID}/feedback", json={"outcome": "lasted_longer"})
    finally:
        app.dependency_overrides.clear()

    assert set(captured["patch"].keys()) == {"feedback_outcome", "feedback_submitted_at"}
