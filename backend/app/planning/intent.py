"""Intent parsing schemas for natural-language satellite planning requests.

Defines the Pydantic schema `ParsedIntent` that captures all structured
fields extracted from a user's free-text planning request.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class BoundingBox(BaseModel):
    """WGS84 bounding box for a geographic target area."""

    sw_lat: float = Field(..., ge=-90.0, le=90.0, description="Southwest latitude")
    sw_lng: float = Field(..., ge=-180.0, le=180.0, description="Southwest longitude")
    ne_lat: float = Field(..., ge=-90.0, le=90.0, description="Northeast latitude")
    ne_lng: float = Field(..., ge=-180.0, le=180.0, description="Northeast longitude")

    @model_validator(mode="after")
    def _bbox_bounds(self) -> "BoundingBox":
        # Normalise: ensure ne is northeast of sw
        if self.ne_lat < self.sw_lat:
            self.sw_lat, self.ne_lat = self.ne_lat, self.sw_lat
        if self.ne_lng < self.sw_lng:
            self.sw_lng, self.ne_lng = self.ne_lng, self.sw_lng
        return self

    def to_dict(self) -> dict[str, float]:
        return {
            "sw_lat": self.sw_lat,
            "sw_lng": self.sw_lng,
            "ne_lat": self.ne_lat,
            "ne_lng": self.ne_lng,
        }


class ConfidenceScores(BaseModel):
    """Per-field confidence scores (0.0–1.0) from the LLM."""

    region_description: float = Field(..., ge=0.0, le=1.0)
    resolution_requirement_m: float = Field(..., ge=0.0, le=1.0)
    time_window_days: float = Field(..., ge=0.0, le=1.0)
    priority: float = Field(..., ge=0.0, le=1.0)

    def to_dict(self) -> dict[str, float]:
        """Convert to a JSON-serialisable dictionary."""
        return {
            "region_description": self.region_description,
            "resolution_requirement_m": self.resolution_requirement_m,
            "time_window_days": self.time_window_days,
            "priority": self.priority,
        }


class ParsedIntent(BaseModel):
    """Structured intent parsed from a user's natural-language planning request."""

    region_description: Optional[str] = None
    bounding_box: Optional[BoundingBox] = None
    event_filter: Optional[str] = None
    resolution_requirement_m: Optional[float] = Field(
        None, gt=0.0, description="Max ground resolution in meters"
    )
    time_window_days: Optional[int] = Field(
        None, ge=1, le=31, description="Planning horizon in days"
    )
    priority: str = Field(
        "normal",
        pattern="^(low|normal|high|urgent)$",
        description="Task priority level",
    )
    sensor_preference: Optional[str] = Field(
        None, pattern="^(optical|multispectral|sar|hyperspectral)$"
    )
    confidence: Optional[ConfidenceScores] = None
    uncertainty_notes: list[str] = Field(
        default_factory=list, description="Free-text uncertainty notes"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-serialisable dictionary."""
        d = {
            "region_description": self.region_description,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
            "event_filter": self.event_filter,
            "resolution_requirement_m": self.resolution_requirement_m,
            "time_window_days": self.time_window_days,
            "priority": self.priority,
            "sensor_preference": self.sensor_preference,
            "confidence": self.confidence.to_dict() if self.confidence else None,
            "uncertainty_notes": self.uncertainty_notes,
        }
        return d


class LLMResponse(BaseModel):
    """Wraps a raw LLM output with metadata."""

    parsed_intent: ParsedIntent
    raw_text: str
