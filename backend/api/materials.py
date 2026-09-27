from fastapi import APIRouter

from engine.material_lookup import list_materials
from models.schemas import MaterialListResponse, MaterialSummary

router = APIRouter(prefix="/materials", tags=["materials"])


def _to_summary(m: dict) -> MaterialSummary:
    return MaterialSummary(
        id=m["id"],
        name=m["name"],
        name_hi=m.get("display_name_hi"),
        category=m["category"],
        otr_cm3_m2_day_atm=m.get("otr_cm3_m2_day_atm"),
        wvtr_g_m2_day=m.get("wvtr_g_m2_day"),
        thickness_range_micron=m.get("thickness_range_micron"),
        cost_tier=m["cost_tier"],
        estimated_cost_per_kg_inr=m.get("estimated_cost_per_kg_inr"),
        recyclability_rating=m["recyclability_rating"],
        typical_use_cases=m.get("typical_use_cases", []),
        confidence=m["confidence"],
    )


@router.get("", response_model=MaterialListResponse)
def get_materials() -> MaterialListResponse:
    """Public. Read-only reference list of all packaging materials in
    packaging_materials.json — the same records already used by the
    recommendation engine and reports, just exposed directly for a standalone
    browsing page. No auth, no per-user data, nothing computed here."""
    return MaterialListResponse(materials=[_to_summary(m) for m in list_materials()])
