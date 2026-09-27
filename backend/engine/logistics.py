"""Source -> destination transport-distance estimation.

Two resolution paths for turning a free-text place name into coordinates:
1. LIVE: OpenStreetMap's Nominatim geocoding API (free, no API key). Used
   first, with a short timeout and an in-memory cache.
2. OFFLINE FALLBACK: fuzzy match against data/major_cities_india.json, a
   static table of ~85 major Indian cities. Used whenever Nominatim fails,
   times out, or returns no result — this is what keeps the feature
   demo-resilient with no network dependency.

Either way, the actual distance is haversine (great-circle / straight-line)
— never a routed driving distance, and never from an external routing API.
This is stated explicitly in the disclaimer this module returns, and is
NOT the same thing as real road distance (which is typically 15-40% longer
depending on terrain and road layout) — callers must not present the
result as a route.

Nominatim usage-policy compliance (https://operations.osmfoundation.org/policies/nominatim/):
- A descriptive User-Agent identifying this application (not a generic/
  default one) is sent on every request — see _USER_AGENT below.
- At most ~1 request/second: _pace_live_request() enforces a minimum gap
  between consecutive live calls, and results are cached in-memory so a
  repeated lookup during testing/a demo never re-hits the API at all.
- No bulk/batch geocoding — this module resolves exactly the two locations
  a single user request asks for, nothing more.
"""

from __future__ import annotations

import difflib
import math
import time
from functools import lru_cache
from typing import Any

import httpx

from engine.recommender import _load_json, _rules

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# Descriptive per Nominatim's usage policy — identifies the app, not a
# generic/default User-Agent. No real contact URL/email is wired in yet
# (this is a hackathon project); add one here before any production use.
_USER_AGENT = "Wrapture/1.0 (SIH PS 26236 packaging-recommendation tool; hackathon project, no production traffic)"
_LIVE_TIMEOUT_SECONDS = 3.5
_MIN_SECONDS_BETWEEN_LIVE_REQUESTS = 1.1  # Nominatim policy: max ~1 req/sec

_geocode_cache: dict[str, tuple[float, float] | None] = {}
_last_live_request_at: float = 0.0


class LocationNotFoundError(Exception):
    """Raised when a location resolves on neither the live nor the offline path."""

    def __init__(self, query: str, suggestions: list[str]):
        self.query = query
        self.suggestions = suggestions
        super().__init__(f"Could not resolve location: {query!r}")


@lru_cache
def _cities() -> list[dict]:
    return _load_json("major_cities_india.json")["cities"]


def _pace_live_request() -> None:
    """Blocks briefly if needed so consecutive live Nominatim calls stay
    under the ~1 req/sec usage-policy ceiling."""
    global _last_live_request_at
    elapsed = time.monotonic() - _last_live_request_at
    if elapsed < _MIN_SECONDS_BETWEEN_LIVE_REQUESTS:
        time.sleep(_MIN_SECONDS_BETWEEN_LIVE_REQUESTS - elapsed)
    _last_live_request_at = time.monotonic()


def _geocode_live(query: str) -> tuple[float, float] | None:
    """Tries OpenStreetMap Nominatim first. Returns None (never raises) on
    any failure — timeout, network error, HTTP error, or no results — so
    the caller always has a clean signal to fall through to the offline
    table. Cached in-memory so repeated lookups (tests, a demo re-running
    the same city pair) don't re-hit the API at all."""
    cache_key = query.strip().lower()
    if cache_key in _geocode_cache:
        return _geocode_cache[cache_key]

    result: tuple[float, float] | None = None
    try:
        _pace_live_request()
        response = httpx.get(
            _NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1, "countrycodes": "in"},
            headers={"User-Agent": _USER_AGENT},
            timeout=_LIVE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        if data:
            result = (float(data[0]["lat"]), float(data[0]["lon"]))
    except (httpx.HTTPError, httpx.TimeoutException, KeyError, ValueError, IndexError):
        result = None

    _geocode_cache[cache_key] = result
    return result


def _fuzzy_match_offline(query: str) -> dict | None:
    """Case-insensitive fuzzy match against every city's name AND aliases
    (e.g. 'Bengaluru' matches the Bangalore record, 'banglore' still
    matches Bangalore via a close-enough cutoff)."""
    needle = query.strip().lower()
    if not needle:
        return None

    searchable: list[tuple[str, dict]] = []
    for city in _cities():
        searchable.append((city["name"].lower(), city))
        for alias in city.get("aliases", []):
            searchable.append((alias.lower(), city))

    # Exact match first (covers common cases cheaply and deterministically).
    for name, city in searchable:
        if name == needle:
            return city

    names = [name for name, _ in searchable]
    close = difflib.get_close_matches(needle, names, n=1, cutoff=0.72)
    if not close:
        return None
    matched_name = close[0]
    return next(city for name, city in searchable if name == matched_name)


def _sample_suggestions(n: int = 6) -> list[str]:
    cities = _cities()
    step = max(1, len(cities) // n)
    return [cities[i]["name"] for i in range(0, len(cities), step)][:n]


def resolve_location(query: str) -> tuple[tuple[float, float], str]:
    """Returns ((lat, lon), "live" | "offline"). Raises LocationNotFoundError
    if the location can't be resolved on either path."""
    live = _geocode_live(query)
    if live is not None:
        return live, "live"

    offline = _fuzzy_match_offline(query)
    if offline is not None:
        return (offline["latitude"], offline["longitude"]), "offline"

    raise LocationNotFoundError(query, _sample_suggestions())


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle (straight-line) distance in km — NOT a road route."""
    earth_radius_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * earth_radius_km * math.asin(math.sqrt(a))


def _round_to_half_day(days: float) -> float:
    return round(days * 2) / 2


def estimate_transport(source: str, destination: str) -> dict[str, Any]:
    """Resolves both locations (live Nominatim first, offline fallback
    second, independently per location) and returns distance/estimated
    transport days. Raises LocationNotFoundError if EITHER location can't
    be resolved on either path — the caller (api/logistics.py) turns that
    into a 422 with the suggestion list attached."""
    rules = _rules()
    logistics_config = rules["logistics"]

    source_point, source_via = resolve_location(source)
    dest_point, dest_via = resolve_location(destination)

    distance_km = haversine_km(source_point[0], source_point[1], dest_point[0], dest_point[1])

    raw_days = distance_km / logistics_config["km_per_transport_day"]
    estimated_transport_days = max(
        logistics_config["min_transport_days"], _round_to_half_day(raw_days)
    )

    # Overall source_used is "live_geocoding" only if BOTH legs resolved live —
    # if either fell back, the result depends on the offline table for at
    # least part of the estimate, so the more conservative disclaimer applies.
    both_live = source_via == "live" and dest_via == "live"
    source_used = "live_geocoding" if both_live else "offline_fallback"

    if source_used == "live_geocoding":
        disclaimer = (
            "Estimated straight-line (not road-route) distance from live location lookup "
            "(OpenStreetMap Nominatim). Actual road transport distance and time will be longer — "
            "use this as a starting estimate, not a routed ETA."
        )
    else:
        disclaimer = (
            "Estimated straight-line (not road-route) distance, using offline city data for at "
            "least one location (live lookup was unavailable or found no match). Actual road "
            "transport distance and time will be longer — use this as a starting estimate, not a "
            "routed ETA."
        )

    return {
        "distance_km": round(distance_km, 1),
        "estimated_transport_days": estimated_transport_days,
        "source_used": source_used,
        "resolved_via": {"source": source_via, "destination": dest_via},
        "disclaimer": disclaimer,
    }
