from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""
    # Service-role key — bypasses Row Level Security entirely. Backend-only, never sent to
    # the frontend. Used ONLY by the two intentionally-public report endpoints (public view
    # + QR code) that have no user token to scope a request by; every other Supabase call in
    # this app uses the caller's own access token instead. See core/supabase_client.py.
    supabase_service_role_key: str = ""
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    # Canonical frontend origin — used to build the /verify/{report_id} URL encoded in each
    # report's QR code. Not related to CORS_ORIGINS (which is about which origins may call
    # this API); this is about which origin the QR code should point a scanner's phone at.
    frontend_url: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
