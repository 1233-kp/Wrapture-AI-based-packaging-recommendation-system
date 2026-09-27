"""Tests for the public GET /faq and POST /faq/match endpoints.

Standalone app with just the faq router — same pattern as
test_public_report.py — so this doesn't pay the commodity-matcher's startup
warm-up cost from the full main.app.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.faq import router as faq_router

app = FastAPI()
app.include_router(faq_router)
client = TestClient(app)


def test_get_faq_list_requires_no_auth():
    res = client.get("/faq")
    assert res.status_code == 200
    assert len(res.json()["faqs"]) == 16


def test_faq_item_shape():
    res = client.get("/faq")
    item = res.json()["faqs"][0]
    assert set(item.keys()) == {"id", "question", "question_hi", "answer", "answer_hi"}


def test_post_faq_match_returns_matched_faq():
    res = client.post("/faq/match", json={"query": "Does the app work in Hindi?"})
    assert res.status_code == 200
    data = res.json()
    assert data["matched"] is True
    assert data["faq"]["id"] == "hindi-support"
    assert data["faq"]["answer"]  # non-empty real answer, not a placeholder


def test_post_faq_match_returns_null_faq_when_unmatched():
    res = client.post("/faq/match", json={"query": "What is the capital of France?"})
    assert res.status_code == 200
    data = res.json()
    assert data["matched"] is False
    assert data["faq"] is None


def test_post_faq_match_rejects_empty_query():
    res = client.post("/faq/match", json={"query": ""})
    assert res.status_code == 422


def test_post_faq_match_requires_no_auth():
    res = client.post("/faq/match", json={"query": "Is this free to use?"})
    assert res.status_code == 200
