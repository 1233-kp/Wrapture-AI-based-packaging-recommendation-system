from fastapi import APIRouter

from engine.faq_matcher import list_faqs, match_faq
from models.schemas import FaqItem, FaqListResponse, FaqMatchRequest, FaqMatchResponse

router = APIRouter(prefix="/faq", tags=["faq"])


@router.get("", response_model=FaqListResponse)
def get_faqs() -> FaqListResponse:
    """Public. Full FAQ list, for the FAQ page's accordion."""
    return FaqListResponse(faqs=[FaqItem(**f) for f in list_faqs()])


@router.post("/match", response_model=FaqMatchResponse)
def post_faq_match(payload: FaqMatchRequest) -> FaqMatchResponse:
    """Public. Template-matches a free-text question against the FAQ list
    using local sentence-transformer embeddings — the same model and
    approach as /commodities/match. Never generates an answer: returns one
    of the existing FAQ answers, or an honest no-match result if nothing
    clears the similarity threshold. This is the FAQ assistant's entire
    backend — there's no LLM call and no external API involved."""
    result = match_faq(payload.query.strip())
    faq = FaqItem(**result["faq"]) if result["faq"] else None
    return FaqMatchResponse(
        query=result["query"],
        matched=result["matched"],
        faq=faq,
        similarity_percent=result["similarity_percent"],
        threshold=result["threshold"],
    )
