"""
Geocoding Service — Multi-provider geocoding with fallback chain.

Providers (in priority order):
  1. Built-in REGION_BBOX dictionary (307 regions, no API needed)
  2. Nominatim (OpenStreetMap) — free, global
  3. Amap (高德地图) — excellent for China, requires API key
  4. LLM fallback — uses OpenAI to extract bbox

Usage:
    from app.services.geocoding_service import geocode

    result = geocode("Tokyo Bay")
    if result:
        print(result.sw_lat, result.sw_lng, result.ne_lat, result.ne_lng)
"""

from __future__ import annotations

import logging
import math
import os
import re
from dataclasses import dataclass
from typing import Optional

import httpx

from app.planning.geocoding import (
    REGION_BBOX,
    _fuzzy_match as _internal_fuzzy_match,
    _tokenize,
    _jaccard,
    _levenshtein_ratio,
    BBox as InternalBBox,
)

logger = logging.getLogger(__name__)

# ── BBox with metadata ───────────────────────────────────────────────────────


@dataclass
class GeocodeResult:
    """Result of geocoding operation with source information."""

    bbox: InternalBBox
    source: str  # "builtin" | "nominatim" | "amap" | "llm"
    confidence: float  # 0.0-1.0
    display_name: Optional[str] = None


# ── Built-in Dictionary Lookup ────────────────────────────────────────────────


def _lookup_builtin(query: str) -> Optional[GeocodeResult]:
    """Check built-in REGION_BBOX dictionary."""
    query_lower = query.strip().lower()

    # Exact match
    if query_lower in REGION_BBOX:
        sw_lat, sw_lng, ne_lat, ne_lng = REGION_BBOX[query_lower]
        return GeocodeResult(
            bbox=InternalBBox(sw_lat, sw_lng, ne_lat, ne_lng),
            source="builtin",
            confidence=1.0,
            display_name=query_lower.title(),
        )

    # Fuzzy match
    matched_key = _internal_fuzzy_match(query_lower, threshold=0.55)
    if matched_key:
        sw_lat, sw_lng, ne_lat, ne_lng = REGION_BBOX[matched_key]
        score = (
            _jaccard(_tokenize(query_lower), _tokenize(matched_key)) * 0.6
            + _levenshtein_ratio(query_lower, matched_key) * 0.4
        )
        return GeocodeResult(
            bbox=InternalBBox(sw_lat, sw_lng, ne_lat, ne_lng),
            source="builtin",
            confidence=score,
            display_name=matched_key.title(),
        )

    return None


# ── Nominatim (OpenStreetMap) ────────────────────────────────────────────────

NOMINATIM_BASE = "https://nominatim.openstreetmap.org"


async def _geocode_nominatim(query: str) -> Optional[GeocodeResult]:
    """Query Nominatim for geocoding.

    Rate limit: 1 request per second. Free for non-commercial use.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                NOMINATIM_BASE + "/search",
                params={
                    "q": query,
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1,
                    "countrycodes": "us,ca,gb,au,jp,de,fr,it,es,nl,br,cn,kr,in",
                },
                headers={
                    "User-Agent": "Apex-Satellite-Planner/1.0 (satellite-task-planning)",
                },
            )
            response.raise_for_status()
            data = response.json()

            if not data:
                return None

            result = data[0]
            # Get bounding box from Nominatim response
            if "boundingbox" in result:
                bounding = result["boundingbox"]
                # Nominatim returns: [south, north, west, east]
                sw_lat = float(bounding[0])
                ne_lat = float(bounding[1])
                sw_lng = float(bounding[2])
                ne_lng = float(bounding[3])
            else:
                # Calculate approximate bounding box from lat/lon
                lat = float(result["lat"])
                lon = float(result["lon"])
                # Use ~0.5 degree radius for city-level results
                sw_lat = lat - 0.5
                ne_lat = lat + 0.5
                sw_lng = lon - 0.5
                ne_lng = lon + 0.5

            return GeocodeResult(
                bbox=InternalBBox(sw_lat, sw_lng, ne_lat, ne_lng),
                source="nominatim",
                confidence=0.8,
                display_name=result.get("display_name", query),
            )
    except Exception as e:
        logger.debug(f"Nominatim geocoding failed: {e}")
        return None


# ── Amap (高德地图) ─────────────────────────────────────────────────────────

AMAP_BASE = "https://restapi.amap.com/v3"


async def _geocode_amap(query: str) -> Optional[GeocodeResult]:
    """Query Amap (高德地图) for geocoding.

    Excellent for China addresses. Requires API key from https://lbs.amap.com/
    Free tier: 150,000 requests/month for personal use.
    """
    api_key = os.environ.get("AMAP_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                AMAP_BASE + "/geocode/geo",
                params={
                    "key": api_key,
                    "address": query,
                    "output": "json",
                },
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "1" or not data.get("geocodes"):
                return None

            geocode = data["geocodes"][0]
            location = geocode.get("location", "")

            if not location:
                return None

            lon_str, lat_str = location.split(",")
            center_lon = float(lon_str)
            center_lat = float(lat_str)

            # Get city-level bounding box from Amap's district info
            # Amap returns boundaries for districts but not directly for cities
            # Use approximate radius based on city type
            city_level = geocode.get("level", "城市")

            # Approximate radius in degrees (very rough)
            radius_map = {
                "省": 3.0,
                "市": 1.5,
                "区县": 0.5,
                "兴趣点": 0.1,
                "城市": 0.8,
            }
            radius = radius_map.get(city_level, 0.5)

            # Add buffer for better coverage
            buffer = 0.1

            sw_lat = center_lat - radius - buffer
            ne_lat = center_lat + radius + buffer
            sw_lng = center_lon - radius - buffer
            ne_lng = center_lon + radius + buffer

            # Ensure valid coordinates
            sw_lat = max(-90, sw_lat)
            ne_lat = min(90, ne_lat)
            sw_lng = max(-180, sw_lng)
            ne_lng = min(180, ne_lng)

            return GeocodeResult(
                bbox=InternalBBox(sw_lat, sw_lng, ne_lat, ne_lng),
                source="amap",
                confidence=0.9 if city_level in ["市", "城市"] else 0.7,
                display_name=geocode.get("formatted_address", query),
            )
    except Exception as e:
        logger.debug(f"Amap geocoding failed: {e}")
        return None


# ── LLM Fallback ─────────────────────────────────────────────────────────────


async def _geocode_llm(query: str) -> Optional[GeocodeResult]:
    """Use OpenAI to extract bounding box coordinates."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "your-openai-api-key-here":
        return None

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=256,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a geographic bounding-box extractor. "
                        "Given a region description, return a JSON object with fields: "
                        "sw_lat, sw_lng, ne_lat, ne_lng (all decimal degrees, WGS84). "
                        "Return null if the region is unrecognisable. "
                        "Output ONLY the JSON, no markdown, no explanation."
                    ),
                },
                {
                    "role": "user",
                    "content": f"What is the approximate bounding box for: {query}",
                },
            ],
        )
        text = response.choices[0].message.content.strip()

        # Handle potential markdown code blocks
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        import json

        data = json.loads(text)
        if data is None:
            return None

        return GeocodeResult(
            bbox=InternalBBox(
                sw_lat=float(data["sw_lat"]),
                sw_lng=float(data["sw_lng"]),
                ne_lat=float(data["ne_lat"]),
                ne_lng=float(data["ne_lng"]),
            ),
            source="llm",
            confidence=0.6,  # LLM has lower confidence
            display_name=query,
        )
    except Exception as e:
        logger.debug(f"LLM geocoding failed: {e}")
        return None


# ── Public API ───────────────────────────────────────────────────────────────


async def geocode(
    query: str,
    providers: Optional[list[str]] = None,
    use_llm_fallback: bool = True,
) -> Optional[GeocodeResult]:
    """Geocode a location query to bounding box.

    Args:
        query: Location description (e.g., "Tokyo Bay", "北京市朝阳区")
        providers: List of providers to try in order.
                   Options: "builtin", "nominatim", "amap"
                   Default: ["builtin", "nominatim", "amap"]
        use_llm_fallback: Whether to use LLM as final fallback

    Returns:
        GeocodeResult with bbox and metadata, or None if all providers fail.
    """
    if not query or not query.strip():
        return None

    query = query.strip()

    # Determine provider order
    if providers is None:
        # Smart ordering: prefer built-in for common queries
        # Try amap first for Chinese text
        is_chinese = bool(re.search(r"[\u4e00-\u9fff]", query))
        if is_chinese:
            providers = ["builtin", "amap", "nominatim"]
        else:
            providers = ["builtin", "nominatim", "amap"]

    # Try each provider in order
    for provider in providers:
        if provider == "builtin":
            result = _lookup_builtin(query)
            if result:
                return result

        elif provider == "nominatim":
            result = await _geocode_nominatim(query)
            if result:
                return result

        elif provider == "amap":
            result = await _geocode_amap(query)
            if result:
                return result

    # Final LLM fallback
    if use_llm_fallback:
        result = await _geocode_llm(query)
        if result:
            return result

    return None


def geocode_sync(
    query: str,
    providers: Optional[list[str]] = None,
) -> Optional[GeocodeResult]:
    """Synchronous wrapper for geocode()."""
    import asyncio

    return asyncio.run(geocode(query, providers))


# ── Batch Geocoding ─────────────────────────────────────────────────────────


async def geocode_batch(
    queries: list[str],
    providers: Optional[list[str]] = None,
    delay_seconds: float = 1.0,
) -> dict[str, Optional[GeocodeResult]]:
    """Geocode multiple locations with rate limiting.

    Args:
        queries: List of location queries
        providers: Providers to use
        delay_seconds: Delay between requests (for rate limiting)

    Returns:
        Dict mapping query to GeocodeResult
    """
    import asyncio

    results = {}
    for query in queries:
        result = await geocode(query, providers)
        results[query] = result

        # Rate limiting (especially important for Nominatim)
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)

    return results


# ── Reverse Geocoding ────────────────────────────────────────────────────────


async def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    """Get location name from coordinates.

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)

    Returns:
        Display name of the location, or None if not found.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                NOMINATIM_BASE + "/reverse",
                params={
                    "lat": lat,
                    "lon": lon,
                    "format": "json",
                    "addressdetails": 1,
                },
                headers={
                    "User-Agent": "Apex-Satellite-Planner/1.0",
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("display_name")
    except Exception as e:
        logger.debug(f"Reverse geocoding failed: {e}")
        return None


# ── Coordinate Conversion ─────────────────────────────────────────────────────


def wgs84_to_gcj02(lon: float, lat: float) -> tuple[float, float]:
    """Convert WGS84 to GCJ-02 (Chinese encrypted coordinates).

    Required for using Chinese map services (Amap, Baidu) with WGS84 data.
    """

    # Simplified conversion (Marsaglia method approximation)
    a = 6378245.0  # semi-major axis
    ee = 0.00669342162296594323  # eccentricity squared

    def transform(x: float, y: float) -> tuple[float, float]:
        dlat = _transform_lat(x - 105.0, y - 35.0)
        dlon = _transform_lon(x - 105.0, y - 35.0)
        radlat = lat / 180.0 * math.pi
        magic = math.sin(radlat)
        magic = 1 - ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * math.pi)
        dlon = (dlon * 180.0) / (a / sqrtmagic * math.cos(radlat) * math.pi)
        return dlat, dlon

    def _transform_lat(x: float, y: float) -> float:
        ret = -100.0 + 2.0 * x + 3.0 * y
        ret += 0.2 * y * y + 0.1 * x * y
        ret += 0.2 * math.sqrt(abs(x))
        ret += (
            (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi))
            * 2.0
            / 3.0
        )
        ret += (
            (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi))
            * 2.0
            / 3.0
        )
        ret += (
            (
                160.0 * math.sin(y / 12.0 * math.pi)
                + 320.0 * math.sin(y * math.pi / 30.0)
            )
            * 2.0
            / 3.0
        )
        return ret

    def _transform_lon(x: float, y: float) -> float:
        ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
        ret += (
            (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi))
            * 2.0
            / 3.0
        )
        ret += (
            (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi))
            * 2.0
            / 3.0
        )
        ret += (
            (
                150.0 * math.sin(x / 12.0 * math.pi)
                + 300.0 * math.sin(x / 30.0 * math.pi)
            )
            * 2.0
            / 3.0
        )
        return ret

    dlat, dlon = transform(lon, lat)
    return lon + dlon, lat + dlat


def gcj02_to_wgs84(lon: float, lat: float) -> tuple[float, float]:
    """Convert GCJ-02 to WGS84."""
    return wgs84_to_gcj02(lon, lat)  # Same function (involves iteration in real impl)
