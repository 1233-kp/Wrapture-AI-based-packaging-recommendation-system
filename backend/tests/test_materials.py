"""Tests for the public, no-auth GET /materials reference endpoint."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.materials import router as materials_router

app = FastAPI()
app.include_router(materials_router)
client = TestClient(app)


def test_materials_endpoint_returns_all_materials():
    res = client.get("/materials")

    assert res.status_code == 200
    data = res.json()
    assert len(data["materials"]) == 13


def test_materials_endpoint_requires_no_auth():
    res = client.get("/materials")
    assert res.status_code == 200


def test_material_summary_has_expected_fields():
    res = client.get("/materials")
    ldpe = next(m for m in res.json()["materials"] if m["id"] == "ldpe")

    assert set(ldpe.keys()) == {
        "id",
        "name",
        "name_hi",
        "category",
        "otr_cm3_m2_day_atm",
        "wvtr_g_m2_day",
        "thickness_range_micron",
        "cost_tier",
        "estimated_cost_per_kg_inr",
        "recyclability_rating",
        "typical_use_cases",
        "confidence",
    }
    assert ldpe["cost_tier"] == "low"
    assert ldpe["otr_cm3_m2_day_atm"] == {"min": 7000, "max": 9000}
    assert "bread bags" in ldpe["typical_use_cases"]


def test_materials_endpoint_omits_internal_scoring_fields():
    """Fields like cost_confidence/material_weight_multiplier/_cost_note are
    internal to the scoring engine — the public reference endpoint shouldn't
    expose them."""
    res = client.get("/materials")
    body_text = res.text

    assert "material_weight_multiplier" not in body_text
    assert "_cost_note" not in body_text
    assert "cost_confidence" not in body_text
