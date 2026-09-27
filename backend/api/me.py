from fastapi import APIRouter, Depends

from core.auth import CurrentUser, get_current_user

router = APIRouter(tags=["auth"])


@router.get("/me")
def get_me(current_user: CurrentUser = Depends(get_current_user)) -> dict:
    """Minimal protected endpoint used to verify the Supabase JWT dependency
    end-to-end: call it with `Authorization: Bearer <supabase access token>`
    after signing in via Google/GitHub on the frontend."""
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "role": current_user.role,
    }
