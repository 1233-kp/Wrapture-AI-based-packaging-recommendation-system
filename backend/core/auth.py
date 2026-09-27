import time
from dataclasses import dataclass

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from core.config import get_settings

# auto_error=False so we can return our own 401 with a clear message instead of
# FastAPI's generic "Not authenticated" when the header is missing.
_bearer_scheme = HTTPBearer(auto_error=False)

# Newer Supabase projects sign access tokens with a rotating asymmetric key
# (ES256) published at this JWKS endpoint instead of a static shared secret.
# Cached in-process; refreshed if a token references a kid we haven't seen yet
# (covers key rotation) or once the cache goes stale.
_JWKS_CACHE_TTL_SECONDS = 600
_jwks_cache: dict = {"keys": [], "fetched_at": 0.0}


@dataclass
class CurrentUser:
    user_id: str
    email: str | None
    role: str | None
    access_token: str


def _fetch_jwks() -> list[dict]:
    settings = get_settings()
    if not settings.supabase_url:
        return []
    url = settings.supabase_url.rstrip("/") + "/auth/v1/.well-known/jwks.json"
    response = httpx.get(url, timeout=5.0)
    response.raise_for_status()
    return response.json().get("keys", [])


def _find_jwk(kid: str) -> dict | None:
    now = time.time()
    stale = now - _jwks_cache["fetched_at"] > _JWKS_CACHE_TTL_SECONDS
    if stale or not _jwks_cache["keys"]:
        _jwks_cache["keys"] = _fetch_jwks()
        _jwks_cache["fetched_at"] = now

    for key in _jwks_cache["keys"]:
        if key.get("kid") == kid:
            return key

    # kid not found — could be a just-rotated key, force one refresh before giving up.
    _jwks_cache["keys"] = _fetch_jwks()
    _jwks_cache["fetched_at"] = time.time()
    for key in _jwks_cache["keys"]:
        if key.get("kid") == kid:
            return key
    return None


def _decode_supabase_jwt(token: str) -> dict:
    settings = get_settings()
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    alg = header.get("alg")
    kid = header.get("kid")

    if alg == "HS256" and not kid:
        # Legacy Supabase projects that still sign with the static JWT secret.
        if not settings.supabase_jwt_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server is missing SUPABASE_JWT_SECRET configuration.",
            )
        signing_key = settings.supabase_jwt_secret
    else:
        # Current Supabase projects: verify against the project's published
        # JWKS using the key id ("kid") from the token header.
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is missing a 'kid' header.",
            )
        signing_key = _find_jwk(kid)
        if signing_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No matching signing key found for this token.",
            )

    try:
        return jwt.decode(
            token,
            signing_key,
            algorithms=[alg],
            audience="authenticated",
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser:
    """Validates a Supabase access token and returns the requesting user.

    Use this as a dependency on any endpoint that must know who the caller is
    (e.g. reading/writing rows in `reports` or `user_profiles`). The `sub`
    claim from the verified token is what should be passed as `user_id` to
    Postgres, so it lines up with `auth.uid()` under RLS.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _decode_supabase_jwt(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim.",
        )

    return CurrentUser(
        user_id=user_id,
        email=payload.get("email"),
        role=payload.get("role"),
        access_token=credentials.credentials,
    )


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser | None:
    """Same as get_current_user, but returns None instead of raising when no
    token is present. Useful for endpoints that work anonymously but behave
    differently for signed-in users (not currently used by /recommend, which
    is fully public, but kept here for endpoints like a future /reports)."""
    if credentials is None:
        return None
    payload = _decode_supabase_jwt(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        return None
    return CurrentUser(
        user_id=user_id,
        email=payload.get("email"),
        role=payload.get("role"),
        access_token=credentials.credentials,
    )
