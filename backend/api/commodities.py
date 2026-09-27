from fastapi import APIRouter, Query

from engine.recommender import list_commodities
from models.schemas import CommodityListResponse, CommoditySummary

router = APIRouter(prefix="/commodities", tags=["commodities"])


def _to_summary(c: dict) -> CommoditySummary:
    return CommoditySummary(
        id=c["id"],
        name=c["name"],
        name_hi=c.get("display_name_hi"),
        category=c["category"],
        confidence=c["confidence"],
    )


@router.get("", response_model=CommodityListResponse)
def get_commodities() -> CommodityListResponse:
    """Public. Full commodity list for a frontend dropdown."""
    return CommodityListResponse(commodities=[_to_summary(c) for c in list_commodities()])


@router.get("/search", response_model=CommodityListResponse)
def search_commodities(q: str = Query(default="", description="Substring match on name or category.")) -> CommodityListResponse:
    """Public. Case-insensitive substring match against name/id/category, for
    frontend auto-fill/type-ahead. Empty query returns the full list."""
    needle = q.strip().lower()
    if not needle:
        return CommodityListResponse(commodities=[_to_summary(c) for c in list_commodities()])

    matches = [
        c
        for c in list_commodities()
        if needle in c["name"].lower() or needle in c["id"].lower() or needle in c["category"].lower()
    ]
    return CommodityListResponse(commodities=[_to_summary(c) for c in matches])
