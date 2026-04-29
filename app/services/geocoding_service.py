"""Geocode a DirectoryOfGood entry using Google Maps Geocoding API.

Priority:
  1. location.zip_code  (most precise — 5-digit US zip or short international code)
  2. location.city + location.state/country
  3. Skip if neither is available or the key is not configured.
"""

import re

import httpx

from app.config import settings

_GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
_US_ZIP_RE = re.compile(r"^\d{5}$")


def _build_address(location: dict | None) -> str | None:
    """Return the best geocodable address string from a location dict, or None."""
    if not location:
        return None

    zip_code = str(location.get("zip_code") or "").strip()
    city = str(location.get("city") or "").strip()
    state = str(location.get("state") or "").strip()
    country = str(location.get("country") or "").strip()

    # Prefer zip when it looks like a real zip/postcode (not a city name or junk).
    if zip_code and len(zip_code) <= 10 and " " not in zip_code:
        # US zip: just the zip code is unambiguous.
        if _US_ZIP_RE.match(zip_code):
            suffix = f", {country}" if country else ""
            return f"{zip_code}{suffix}"
        # Non-US short code: add country context.
        if country:
            return f"{zip_code}, {country}"

    # Fall back to city + state/country.
    parts = [p for p in [city, state, country] if p]
    return ", ".join(parts) if parts else None


async def geocode_location(location: dict | None) -> tuple[float, float] | None:
    """Return (latitude, longitude) for the given location dict, or None on failure."""
    api_key = settings.GOOGLE_MAPS_GEOCODING_API_KEY
    if not api_key:
        return None

    address = _build_address(location)
    if not address:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                _GEOCODING_URL,
                params={"address": address, "key": api_key},
            )
        data = resp.json()
        if data.get("status") != "OK" or not data.get("results"):
            return None
        loc = data["results"][0]["geometry"]["location"]
        return float(loc["lat"]), float(loc["lng"])
    except Exception:
        return None
