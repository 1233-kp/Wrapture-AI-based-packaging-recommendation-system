from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from core.auth import CurrentUser, get_current_user
from core.supabase_client import (
    SupabaseRestError,
    delete_report_row,
    get_report,
    get_report_service_role,
    insert_cold_chain_event,
    insert_report,
    list_cold_chain_events,
    list_reports,
    update_report,
)
from engine.cold_chain import recalculate_after_excursion
from engine.material_lookup import find_material
from engine.pdf_export import build_report_pdf
from engine.qr_code import generate_qr_png_bytes
from models.schemas import (
    ColdChainEvent,
    ColdChainEventListResponse,
    ColdChainExcursionRequest,
    ColdChainExcursionResponse,
    PublicReportView,
    Report,
    ReportCreateRequest,
    ReportFeedbackRequest,
    ReportListResponse,
)

router = APIRouter(prefix="/reports", tags=["reports"])


def _to_public_view(row: dict) -> PublicReportView:
    """Builds the deliberately-narrow public view from a full report row —
    the one place that decides exactly what's safe to expose with no auth."""
    recommendation = row.get("recommendation") or {}
    top = (recommendation.get("recommendations") or [{}])[0]
    material = find_material(top.get("material_id", "")) or {}

    report_id = str(row["id"])
    return PublicReportView(
        trace_id=f"PSA-{report_id.replace('-', '')[:8].upper()}",
        commodity_name=row.get("commodity_name", "Unknown commodity"),
        material_name=top.get("material_name", "Unknown material"),
        otr_cm3_m2_day_atm=material.get("otr_cm3_m2_day_atm"),
        wvtr_g_m2_day=material.get("wvtr_g_m2_day"),
        thickness_range_micron=material.get("thickness_range_micron"),
        sustainability_score=top.get("sustainability_score", 0),
        generated_at=row["created_at"],
    )


@router.post("", response_model=Report, status_code=status.HTTP_201_CREATED)
def post_report(
    payload: ReportCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> Report:
    """Protected. Saves a recommendation (normally the body of a prior
    POST /recommend/detailed call) to the caller's own `reports` row.

    `user_id` is taken from the verified token, never from the request body,
    so a caller cannot save a report under someone else's account even if
    they tried to forge the field — and the RLS insert policy would reject a
    mismatched user_id anyway.
    """
    try:
        row = insert_report(
            current_user.access_token,
            {
                "user_id": current_user.user_id,
                "commodity_name": payload.commodity_name,
                "input_conditions": payload.input_conditions,
                "recommendation": payload.recommendation,
            },
        )
    except SupabaseRestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.detail) from exc
    return Report(**row)


@router.get("", response_model=ReportListResponse)
def get_reports(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(get_current_user),
) -> ReportListResponse:
    """Protected. Lists the caller's own saved reports, most recent first.
    RLS on the `reports` table means this can never return another user's
    rows, regardless of what's passed here."""
    try:
        rows, total = list_reports(current_user.access_token, limit=limit, offset=offset)
    except SupabaseRestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.detail) from exc
    return ReportListResponse(
        reports=[Report(**row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> Response:
    """Protected. Deletes one of the caller's own reports. Ownership is
    enforced by the reports_delete_own RLS policy — a report_id belonging to
    someone else simply matches zero rows and this is a silent 204 no-op,
    same "don't confirm existence" behavior as the other report endpoints."""
    try:
        delete_report_row(current_user.access_token, report_id)
    except SupabaseRestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.detail) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{report_id}/feedback", response_model=Report)
def submit_report_feedback(
    report_id: str,
    payload: ReportFeedbackRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> Report:
    """Protected. Pure data capture — 'was this accurate?' — for the
    caller's own report. Nothing in this codebase reads feedback_outcome to
    retrain a model or auto-adjust future recommendations; it's stored for
    later human review only. Optional: a report has no feedback until the
    user explicitly submits it, and viewing/exporting a report never
    requires it.

    Ownership is enforced by the reports_update_own RLS policy — a
    report_id belonging to someone else simply matches zero rows, which we
    report as 404 rather than confirming whether the id exists."""
    try:
        row = update_report(
            current_user.access_token,
            report_id,
            {"feedback_outcome": payload.outcome, "feedback_submitted_at": datetime.now(UTC).isoformat()},
        )
    except SupabaseRestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.detail) from exc

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return Report(**row)


@router.post("/{report_id}/cold-chain-event", response_model=ColdChainExcursionResponse, status_code=status.HTTP_201_CREATED)
def log_cold_chain_event(
    report_id: str,
    payload: ColdChainExcursionRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ColdChainExcursionResponse:
    """Protected. Manual entry only — no IoT/sensor integration. Logs a
    temperature excursion against the caller's own saved report and
    recalculates remaining shelf life by reusing the existing Q10 model in
    engine/shelf_life.py (via engine/cold_chain.py) — scoring/ranking logic
    is never touched.

    This INSERTs a new cold_chain_events row; it never modifies the
    original report or an earlier logged event, so report history stays
    intact and every excursion has its own permanent record."""
    try:
        row = get_report(current_user.access_token, report_id)
    except SupabaseRestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.detail) from exc

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    result = recalculate_after_excursion(row, payload.temperature_reached_c, payload.duration_hours, payload.lang)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Can't recalculate shelf life for this report's commodity (unrecognized commodity or no "
            "temperature model for its category).",
        )

    try:
        event_row = insert_cold_chain_event(
            current_user.access_token,
            {
                "report_id": report_id,
                "user_id": current_user.user_id,
                "temperature_reached_c": payload.temperature_reached_c,
                "duration_hours": payload.duration_hours,
                "remaining_shelf_life_days": result["remaining_shelf_life_days"],
                "action_urgent": result["action_urgent"],
            },
        )
    except SupabaseRestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.detail) from exc

    return ColdChainExcursionResponse(
        event=ColdChainEvent(**event_row),
        action_message=result["action_message"],
        explanation=result["explanation"],
        disclaimer=result["disclaimer"],
    )


@router.get("/{report_id}/cold-chain-events", response_model=ColdChainEventListResponse)
def get_cold_chain_events(
    report_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> ColdChainEventListResponse:
    """Protected. Lists every excursion previously logged against the
    caller's own report, most recent first — the append-only history
    logging an event creates."""
    try:
        rows = list_cold_chain_events(current_user.access_token, report_id)
    except SupabaseRestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.detail) from exc
    return ColdChainEventListResponse(events=[ColdChainEvent(**r) for r in rows])


@router.get("/{report_id}/export")
def export_report(
    report_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> Response:
    """Protected. Returns a PDF summary of one report. Ownership is enforced
    by RLS: the underlying query is already scoped to the caller's own rows,
    so a report_id belonging to someone else simply comes back empty here —
    which we report as 404, not 403, to avoid confirming whether the id
    exists at all."""
    try:
        row = get_report(current_user.access_token, report_id)
    except SupabaseRestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.detail) from exc

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    pdf_bytes = build_report_pdf(row)
    filename = f"wrapture-report-{report_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{report_id}/public", response_model=PublicReportView)
def get_report_public(report_id: str) -> PublicReportView:
    """Public — no auth. Intentionally bypasses per-user RLS via the
    service_role key (see core/supabase_client.get_report_service_role) because
    this endpoint is *meant* to be reachable by anyone with a report id — e.g.
    a procurement auditor or supply-chain partner scanning the QR code on a
    printed report or product batch, with no Wrapture account of their own.

    This is not a privacy hole: the row fetched with elevated privileges is
    immediately narrowed to PublicReportView before it ever leaves this
    function (see _to_public_view) — no user_id, no email, no account
    information of any kind, regardless of what's in the underlying row.
    """
    try:
        row = get_report_service_role(report_id)
    except SupabaseRestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.detail) from exc

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    return _to_public_view(row)


@router.get("/{report_id}/qrcode")
def get_report_qrcode(report_id: str) -> Response:
    """Public — no auth. The QR image only ever encodes a URL to the
    already-public /verify page (see engine/qr_code.py), so serving it
    without auth exposes nothing beyond what /public already exposes."""
    try:
        row = get_report_service_role(report_id)
    except SupabaseRestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.detail) from exc

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    png_bytes = generate_qr_png_bytes(report_id)
    return Response(content=png_bytes, media_type="image/png")
