from fastapi import APIRouter

from engine.commodity_matcher import match_commodities
from models.schemas import CommodityMatchRequest, CommodityMatchResponse

router = APIRouter(prefix="/commodities", tags=["commodity-match"])


@router.post("/match", response_model=CommodityMatchResponse)
def post_commodity_match(payload: CommodityMatchRequest) -> CommodityMatchResponse:
    """Public. Free-text fallback for commodities not in the commodities database —
    embeds the query locally (sentence-transformers, no external API call) and
    returns the top 3 existing commodities by cosine similarity, each with the
    properties that would be borrowed if selected. Does not touch /recommend or
    /recommend/detailed: selecting a match just means calling those endpoints
    with that existing commodity's id, same as picking it from the dropdown."""
    result = match_commodities(payload.query.strip())
    return CommodityMatchResponse(**result)
