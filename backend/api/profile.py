from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import CurrentUser, get_current_user
from core.supabase_client import SupabaseRestError, get_profile, update_profile
from models.schemas import ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_my_profile(current_user: CurrentUser = Depends(get_current_user)) -> ProfileResponse:
    """Protected. Reads the caller's own user_profiles row (auto-created on
    signup by the on_auth_user_created trigger — see /supabase/migrations)."""
    try:
        row = get_profile(current_user.access_token, current_user.user_id)
    except SupabaseRestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.detail) from exc

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile row found for this user yet.",
        )
    return ProfileResponse(**row)


@router.patch("", response_model=ProfileResponse)
def patch_my_profile(
    payload: ProfileUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ProfileResponse:
    """Protected. Updates only the fields provided; omitted fields are left
    unchanged. Scoped to the caller's own row by both the query filter here
    and, redundantly, by the RLS update policy."""
    patch = payload.model_dump(exclude_none=True)
    if not patch:
        return get_my_profile(current_user)

    try:
        row = update_profile(current_user.access_token, current_user.user_id, patch)
    except SupabaseRestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.detail) from exc
    return ProfileResponse(**row)
