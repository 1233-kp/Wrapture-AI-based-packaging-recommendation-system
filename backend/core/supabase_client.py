"""Thin PostgREST client for the Supabase `reports` and `user_profiles` tables.

Every call forwards the caller's own (already-verified, see core/auth.py)
Supabase access token as the Authorization header, so Postgres Row Level
Security — not this file — is what actually enforces "you can only touch your
own rows". That keeps the authorization logic in exactly one place (the RLS
policies in /supabase/migrations) instead of duplicating it here and risking
the two drifting apart.

The one deliberate exception is `get_report_service_role`, used only by the
two intentionally-public report endpoints (no user token exists to scope those
requests by) — see its docstring for why that's safe.
"""

from typing import Any

import httpx
from fastapi import HTTPException, status

from core.config import get_settings


class SupabaseRestError(Exception):
    def __init__(self, status_code: int, detail: Any):
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


def _rest_url(path: str) -> str:
    settings = get_settings()
    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server is missing SUPABASE_URL configuration.",
        )
    return f"{settings.supabase_url.rstrip('/')}/rest/v1/{path.lstrip('/')}"


def _headers(access_token: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    settings = get_settings()
    if not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server is missing SUPABASE_ANON_KEY configuration.",
        )
    headers = {
        "apikey": settings.supabase_anon_key,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    if extra:
        headers.update(extra)
    return headers


def _request(
    method: str,
    path: str,
    access_token: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: Any = None,
    extra_headers: dict[str, str] | None = None,
) -> httpx.Response:
    try:
        response = httpx.request(
            method,
            _rest_url(path),
            headers=_headers(access_token, extra_headers),
            params=params,
            json=json_body,
            timeout=10.0,
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach Supabase: {exc}",
        ) from exc

    if response.status_code >= 400:
        raise SupabaseRestError(response.status_code, _safe_json(response))
    return response


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text


# ---------------------------------------------------------------------------
# reports
# ---------------------------------------------------------------------------


def insert_report(access_token: str, row: dict[str, Any]) -> dict[str, Any]:
    response = _request(
        "POST",
        "reports",
        access_token,
        json_body=row,
        extra_headers={"Prefer": "return=representation"},
    )
    rows = response.json()
    return rows[0]


def list_reports(access_token: str, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
    response = _request(
        "GET",
        "reports",
        access_token,
        params={
            "select": "*",
            "order": "created_at.desc",
            "limit": limit,
            "offset": offset,
        },
        extra_headers={"Prefer": "count=exact"},
    )
    rows = response.json()
    total = _parse_content_range_total(response.headers.get("content-range"), fallback=len(rows))
    return rows, total


def get_report(access_token: str, report_id: str) -> dict[str, Any] | None:
    response = _request(
        "GET",
        "reports",
        access_token,
        params={"select": "*", "id": f"eq.{report_id}"},
    )
    rows = response.json()
    return rows[0] if rows else None


def update_report(access_token: str, report_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    """PATCHes a report by id, scoped to the caller's own token — same
    RLS-enforced-ownership pattern as get_report/delete_report_row. Used for
    the report-feedback feature (feedback_outcome/feedback_submitted_at);
    never touches commodity_name/input_conditions/recommendation."""
    response = _request(
        "PATCH",
        "reports",
        access_token,
        params={"id": f"eq.{report_id}"},
        json_body=patch,
        extra_headers={"Prefer": "return=representation"},
    )
    rows = response.json()
    return rows[0] if rows else None


def delete_report_row(access_token: str, report_id: str) -> None:
    """Deletes a report by id, scoped to the caller's own token as usual.

    Ownership is enforced by the reports_delete_own RLS policy, not here — a
    report_id belonging to someone else simply matches zero rows under RLS,
    so this is a silent no-op rather than an error either way. That mirrors
    get_report()'s existing "don't confirm whether an id exists" behavior.
    """
    _request(
        "DELETE",
        "reports",
        access_token,
        params={"id": f"eq.{report_id}"},
    )


def _service_role_headers() -> dict[str, str]:
    settings = get_settings()
    if not settings.supabase_service_role_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server is missing SUPABASE_SERVICE_ROLE_KEY configuration.",
        )
    return {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
    }


def get_report_service_role(report_id: str) -> dict[str, Any] | None:
    """Fetches a report by id using the service_role key, bypassing RLS entirely.

    INTENTIONAL exception to this file's "always use the caller's own token" rule
    (see module docstring). This exists only for GET /reports/{id}/public and
    GET /reports/{id}/qrcode — both are designed to be reachable by anyone with a
    report id (e.g. via a scanned QR code), with no Supabase session at all, so
    there's no user token to scope the request by. Ownership/privacy is instead
    enforced at the call site by returning only a narrow, deliberately-public
    subset of fields (see api/reports.py) — never the full row, never user_id.
    """
    try:
        response = httpx.get(
            _rest_url("reports"),
            headers=_service_role_headers(),
            params={"select": "*", "id": f"eq.{report_id}"},
            timeout=10.0,
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach Supabase: {exc}",
        ) from exc

    if response.status_code >= 400:
        raise SupabaseRestError(response.status_code, _safe_json(response))

    rows = response.json()
    return rows[0] if rows else None


def _parse_content_range_total(content_range: str | None, fallback: int) -> int:
    # PostgREST format: "0-9/42" or "*/0" when empty.
    if not content_range or "/" not in content_range:
        return fallback
    total_part = content_range.split("/")[-1]
    return int(total_part) if total_part.isdigit() else fallback


# ---------------------------------------------------------------------------
# cold_chain_events
# ---------------------------------------------------------------------------


def insert_cold_chain_event(access_token: str, row: dict[str, Any]) -> dict[str, Any]:
    response = _request(
        "POST",
        "cold_chain_events",
        access_token,
        json_body=row,
        extra_headers={"Prefer": "return=representation"},
    )
    rows = response.json()
    return rows[0]


def list_cold_chain_events(access_token: str, report_id: str) -> list[dict[str, Any]]:
    response = _request(
        "GET",
        "cold_chain_events",
        access_token,
        params={"select": "*", "report_id": f"eq.{report_id}", "order": "created_at.desc"},
    )
    return response.json()


# ---------------------------------------------------------------------------
# user_profiles
# ---------------------------------------------------------------------------


def get_profile(access_token: str, user_id: str) -> dict[str, Any] | None:
    response = _request(
        "GET",
        "user_profiles",
        access_token,
        params={"select": "*", "user_id": f"eq.{user_id}"},
    )
    rows = response.json()
    return rows[0] if rows else None


def update_profile(access_token: str, user_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    response = _request(
        "PATCH",
        "user_profiles",
        access_token,
        params={"user_id": f"eq.{user_id}"},
        json_body=patch,
        extra_headers={"Prefer": "return=representation"},
    )
    rows = response.json()
    return rows[0]
