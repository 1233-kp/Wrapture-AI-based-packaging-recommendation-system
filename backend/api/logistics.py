from fastapi import APIRouter, HTTPException, status

from engine.logistics import LocationNotFoundError, estimate_transport
from models.schemas import ResolvedVia, TransportEstimateRequest, TransportEstimateResponse

router = APIRouter(prefix="/logistics", tags=["logistics"])


@router.post("/estimate-transport-days", response_model=TransportEstimateResponse)
def post_estimate_transport_days(payload: TransportEstimateRequest) -> TransportEstimateResponse:
    """Public endpoint — no auth required.

    Estimates transport days between two free-text locations: geocodes both
    via live OpenStreetMap Nominatim lookup first, falling back independently
    per location to a static offline table of major Indian cities
    (data/major_cities_india.json) if Nominatim fails, times out, or finds no
    match. Distance is always haversine (straight-line), computed locally —
    never a routed driving distance from an external API. Purely additive:
    feeds a suggested value into the existing expected_transport_days input,
    never overrides it automatically.

    422 if a location can't be resolved on either path — the response body
    includes a few example cities from the offline table to try instead.
    """
    try:
        result = estimate_transport(payload.source, payload.destination)
    except LocationNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": f"Could not find a location matching '{err.query}'.",
                "unresolved_location": err.query,
                "suggestions": err.suggestions,
            },
        ) from err

    return TransportEstimateResponse(
        distance_km=result["distance_km"],
        estimated_transport_days=result["estimated_transport_days"],
        source_used=result["source_used"],
        resolved_via=ResolvedVia(**result["resolved_via"]),
        disclaimer=result["disclaimer"],
    )
