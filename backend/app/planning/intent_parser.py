"""Intent parser — converts natural-language planning requests into ParsedIntent.

Uses an LLM (OpenAI gpt-4o-mini) with a structured prompt to extract:
  - region description
  - event filter
  - time window (days)
  - resolution requirement (m)
  - priority
  - sensor preference
  - confidence scores

Includes a keyword-based fallback when LLM is unavailable.
"""

from __future__ import annotations

import re
from typing import Optional

from openai import OpenAI

from app.planning.geocoding import geocode_region
from app.planning.intent import BoundingBox, ConfidenceScores, ParsedIntent


class IntentParser:
    """Parse natural-language planning requests into structured ParsedIntent.

    Args:
        api_key: OpenAI API key. If empty, falls back to keyword-based parsing.
        model: OpenAI model name.
        max_retries: Max LLM retries on failure.
    """

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(
        self,
        api_key: str = "",
        model: str = DEFAULT_MODEL,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> Optional[OpenAI]:
        """Lazy-load the OpenAI client."""
        if self._client is None and self.api_key:
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def parse(
        self, raw_input: str, satellites: list[dict] | None = None
    ) -> ParsedIntent:
        """Parse a user's natural-language planning request.

        Args:
            raw_input: Free-text request from the user.
            satellites: Optional list of available satellite dicts for context.

        Returns:
            A ParsedIntent with structured fields.
        """
        # Tier 1: LLM parsing
        if self.client:
            intent = self._parse_with_llm(raw_input, satellites)
            if intent is not None:
                return intent

        # Tier 2: Keyword-based fallback
        return self._parse_fallback(raw_input)

    def _parse_with_llm(
        self, raw_input: str, satellites: list[dict] | None = None
    ) -> Optional[ParsedIntent]:
        """Call OpenAI to extract structured intent fields."""
        prompt = self._build_prompt(raw_input, satellites)
        client = self.client
        if client is None:
            return None
        for _attempt in range(self.max_retries):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    temperature=0.1,
                    max_tokens=512,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a satellite planning intent parser.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                )
                content = response.choices[0].message.content.strip()
                intent = self._parse_llm_response(content)
                if intent is not None:
                    return intent
            except Exception:
                continue

        # All retries failed — fall through to fallback
        return None

    def _build_prompt(
        self, raw_input: str, satellites: list[dict] | None = None
    ) -> str:
        """Build the LLM prompt for intent parsing."""
        sat_info = ""
        if satellites:
            sat_lines = []
            for s in satellites:
                name = s.get("name", "unknown")
                res = s.get("max_resolution_m", "?")
                payload = s.get("payload_type", "?")
                sat_lines.append(f"- {name}: resolution={res}m, payload={payload}")
            sat_info = "\n\nAvailable satellites:\n" + "\n".join(sat_lines)

        return f"""You are a satellite task planning intent parser. Extract structured fields from the user's request.

Request: "{raw_input}"

{sat_info}

Return a JSON object with the following fields (use null if not specified):
- region_description: string (the geographic target)
- event_filter: string or null (e.g. "flood", "wildfire", null if none)
- resolution_requirement_m: number or null (max ground resolution in meters)
- time_window_days: integer or null (planning horizon in days, 1-31)
- priority: string (one of: "low", "normal", "high", "urgent")
- sensor_preference: string or null (one of: "optical", "multispectral", "sar", "hyperspectral")
- confidence: object with keys region_description, resolution_requirement_m, time_window_days, priority (each 0.0-1.0)
- uncertainty_notes: array of strings (free-text notes about ambiguity)

Only output the JSON object, no markdown formatting, no explanations."""

    def _parse_llm_response(self, content: str) -> Optional[ParsedIntent]:
        """Parse the LLM's JSON response into a ParsedIntent."""
        try:
            import json

            data = json.loads(content)
        except json.JSONDecodeError:
            return None

        confidence_data = data.get("confidence", {})
        confidence = None
        if confidence_data:
            try:
                confidence = ConfidenceScores(
                    region_description=max(
                        0.0,
                        min(1.0, float(confidence_data.get("region_description", 0.5))),
                    ),
                    resolution_requirement_m=max(
                        0.0,
                        min(
                            1.0,
                            float(confidence_data.get("resolution_requirement_m", 0.5)),
                        ),
                    ),
                    time_window_days=max(
                        0.0,
                        min(1.0, float(confidence_data.get("time_window_days", 0.5))),
                    ),
                    priority=max(
                        0.0, min(1.0, float(confidence_data.get("priority", 0.5)))
                    ),
                )
            except (TypeError, ValueError):
                confidence = None

        intent = ParsedIntent(
            region_description=data.get("region_description"),
            event_filter=data.get("event_filter"),
            resolution_requirement_m=data.get("resolution_requirement_m"),
            time_window_days=data.get("time_window_days"),
            priority=data.get("priority", "normal"),
            sensor_preference=data.get("sensor_preference"),
            confidence=confidence,
            uncertainty_notes=data.get("uncertainty_notes", []),
        )

        # Validate and fix common issues
        if intent.priority not in ("low", "normal", "high", "urgent"):
            intent.priority = "normal"
        if intent.sensor_preference and intent.sensor_preference not in (
            "optical",
            "multispectral",
            "sar",
            "hyperspectral",
        ):
            intent.sensor_preference = None

        return intent

    def _parse_fallback(self, raw_input: str) -> ParsedIntent:
        """Keyword-based fallback parser when LLM is unavailable."""
        text = raw_input.lower().strip()
        notes = []

        # ── Region detection ──────────────────────────────────────────────────
        region = None
        region_conf = 0.0

        # Try common geographic patterns
        # Pattern: "image [region]" or "photo [region]" or "[region] area"
        # Extract potential region phrases (2-4 word chunks)
        words = text.split()
        for start in range(len(words) - 1):
            for end in range(start + 2, min(start + 5, len(words) + 1)):
                phrase = " ".join(words[start:end])
                bbox = geocode_region(phrase)
                if bbox and bbox.area_km2() > 100:  # Filter out very small areas
                    region = phrase
                    region_conf = 0.7
                    break
            if region:
                break

        if not region:
            # Single word fallback
            for word in words:
                bbox = geocode_region(word)
                if bbox:
                    region = word
                    region_conf = 0.5
                    break
            notes.append(
                f"No precise region detected; used fallback for '{region}'"
                if region
                else "No region detected"
            )

        # ── Event filter ──────────────────────────────────────────────────────
        event = None
        event_keywords = [
            "flood",
            "wildfire",
            "fire",
            "hurricane",
            "typhoon",
            "earthquake",
            "tsunami",
            "volcano",
            "drought",
            "disaster",
            "incident",
            "emergency",
        ]
        for kw in event_keywords:
            if kw in text:
                event = kw
                break

        # ── Time window ───────────────────────────────────────────────────────
        time_window = None
        time_conf = 0.0

        # Patterns: "next N days", "next week", "in N hours", "for N days"
        match = re.search(r"next\s+(\d+)\s*days?", text)
        if match:
            time_window = int(match.group(1))
            time_conf = 0.9
        else:
            match = re.search(r"next\s+week", text)
            if match:
                time_window = 7
                time_conf = 0.8
            else:
                match = re.search(r"(\d+)\s*days?", text)
                if match:
                    time_window = min(31, int(match.group(1)))
                    time_conf = 0.7
            if not time_window:
                time_window = 7  # Default 1 week
                time_conf = 0.3
                notes.append("Defaulted to 7-day planning horizon")

        # ── Resolution ────────────────────────────────────────────────────────
        resolution = None
        res_conf = 0.0

        match = re.search(
            r"resolution\s*(?:of\s*)?(?:better than|<|less than)\s*(\d+(?:\.\d+)?)\s*m",
            text,
        )
        if match:
            resolution = float(match.group(1))
            res_conf = 0.9
        else:
            match = re.search(r"resolution\s*(\d+(?:\.\d+)?)\s*meters?", text)
            if match:
                resolution = float(match.group(1))
                res_conf = 0.8
            else:
                # Look for resolution-like numbers with "m" unit
                match = re.search(r"(\d+(?:\.\d+)?)\s*meter", text)
                if match:
                    val = float(match.group(1))
                    if 0.1 <= val <= 100:
                        resolution = val
                        res_conf = 0.6

        # ── Priority ──────────────────────────────────────────────────────────
        priority = "normal"
        pri_conf = 0.5
        if "urgent" in text or "emergency" in text or "asap" in text:
            priority = "urgent"
            pri_conf = 0.95
        elif "high" in text:
            priority = "high"
            pri_conf = 0.85
        elif "low" in text and "low priority" in text.lower():
            priority = "low"
            pri_conf = 0.8

        # ── Sensor preference ─────────────────────────────────────────────────
        sensor = None
        sensor_keywords = {
            "optical": ["optical"],
            "multispectral": ["multispectral", "multi-spectral", "msi"],
            "sar": ["sar", "synthetic aperture"],
            "hyperspectral": ["hyperspectral", "hsi"],
        }
        for sensor_type, keywords in sensor_keywords.items():
            if any(kw in text for kw in keywords):
                sensor = sensor_type
                break

        # ── Build intent ──────────────────────────────────────────────────────
        bounding_box = None
        if region:
            bbox_obj = geocode_region(region)
            if bbox_obj:
                bounding_box = BoundingBox(
                    sw_lat=bbox_obj.sw_lat,
                    sw_lng=bbox_obj.sw_lng,
                    ne_lat=bbox_obj.ne_lat,
                    ne_lng=bbox_obj.ne_lng,
                )

        return ParsedIntent(
            region_description=region,
            bounding_box=bounding_box,
            event_filter=event,
            resolution_requirement_m=resolution,
            time_window_days=time_window,
            priority=priority,
            sensor_preference=sensor,
            confidence=ConfidenceScores(
                region_description=region_conf,
                resolution_requirement_m=res_conf,
                time_window_days=time_conf,
                priority=pri_conf,
            ),
            uncertainty_notes=notes,
        )


# Module-level singleton for FastAPI dependency injection
_parser_instance: Optional[IntentParser] = None


def get_intent_parser() -> IntentParser:
    """Return (and lazily initialise) the global IntentParser."""
    global _parser_instance
    if _parser_instance is None:
        api_key = ""
        try:
            import os

            api_key = os.environ.get("OPENAI_API_KEY", "")
        except Exception:
            pass
        _parser_instance = IntentParser(api_key=api_key)
    return _parser_instance
