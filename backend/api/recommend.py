from fastapi import APIRouter, HTTPException, status

from engine.recommender import list_commodities, recommend, recommend_detailed
from models.schemas import (
    CommoditySummary,
    DetailedMaterialRecommendation,
    DetailedRecommendRequest,
    DetailedRecommendResponse,
    MapGasGuidance,
    MaterialRecommendation,
    MlAgreement,
    RecommendRequest,
    RecommendResponse,
    ShelfLifePrediction,
)

router = APIRouter(tags=["recommend"])


def _unknown_commodity_error(commodity_id: str) -> HTTPException:
    known_ids = sorted(c["id"] for c in list_commodities())
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "message": f"Unknown commodity '{commodity_id}'.",
            "known_commodity_ids": known_ids,
        },
    )


@router.post("/recommend", response_model=RecommendResponse)
def post_recommend(payload: RecommendRequest) -> RecommendResponse:
    """Public endpoint — no auth required. Anyone can try the tool.

    Ranks packaging materials for the given commodity and returns the top 3
    matches with per-material rationale and warnings. Saving a report against
    a signed-in user's account is a separate, authenticated concern (not this
    endpoint) — see /backend/core/auth.py for the JWT dependency to use there.
    """
    result = recommend(
        commodity_id_or_name=payload.commodity_id,
        budget_tier=payload.budget_tier,
        prioritize_sustainability=payload.prioritize_sustainability,
        expected_transport_days=payload.expected_transport_days,
        ambient_temperature_c=payload.ambient_temperature_c,
        lang=payload.lang,
    )
    if result is None:
        raise _unknown_commodity_error(payload.commodity_id)

    return RecommendResponse(
        commodity=CommoditySummary(**result["commodity"]),
        recommendations=[MaterialRecommendation(**r) for r in result["recommendations"]],
        disclaimer=result["disclaimer"],
    )


@router.post("/recommend/detailed", response_model=DetailedRecommendResponse)
def post_recommend_detailed(payload: DetailedRecommendRequest) -> DetailedRecommendResponse:
    """Public endpoint — no auth required.

    Same ranking as /recommend, enriched with a structured match_breakdown per
    option (which commodity property was checked against which packaging
    property, and how well it fit), a trade_off_summary comparing each option
    to the top pick, a 0-100 sustainability_score, propagated confidence
    levels, general MAP gas guidance for fresh produce, and a corroborating
    ml_confidence_score per option plus a top-level ml_agreement note from a
    supervised model trained to approximate the rules engine's scoring
    pattern (see /backend/training) — ranking is still driven entirely by the
    rules engine; the ML signal never reorders or overrides it. Also includes
    per-option compliance_notes: informational regulatory-consideration flags
    from a small rule set (see /backend/data/compliance_rules.json) — not a
    certified compliance check, and never affects score/ranking either. Also
    includes a top-level shelf_life_prediction (Q10 temperature-coefficient
    method) when ambient_temperature_c is supplied — a temperature-adjusted
    estimate layered on the commodity's own typical shelf life, not a new
    lab-measured figure; null if no storage temperature was given.
    """
    result = recommend_detailed(
        commodity_id_or_name=payload.commodity_id,
        budget_tier=payload.budget_tier,
        prioritize_sustainability=payload.prioritize_sustainability,
        expected_transport_days=payload.expected_transport_days,
        ambient_temperature_c=payload.ambient_temperature_c,
        lang=payload.lang,
    )
    if result is None:
        raise _unknown_commodity_error(payload.commodity_id)

    return DetailedRecommendResponse(
        commodity=CommoditySummary(**result["commodity"]),
        recommendations=[DetailedMaterialRecommendation(**r) for r in result["recommendations"]],
        map_gas_guidance=MapGasGuidance(**result["map_gas_guidance"]),
        regulatory_note=result["regulatory_note"],
        government_scheme_note=result["government_scheme_note"],
        ml_agreement=MlAgreement(**result["ml_agreement"]) if result["ml_agreement"] else None,
        disclaimer=result["disclaimer"],
        compliance_disclaimer=result["compliance_disclaimer"],
        shelf_life_prediction=(
            ShelfLifePrediction(**result["shelf_life_prediction"]) if result["shelf_life_prediction"] else None
        ),
    )
