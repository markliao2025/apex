"""Planning-related Pydantic schemas for Apex."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    sw_lat: float = Field(..., ge=-90, le=90)
    sw_lng: float = Field(..., ge=-180, le=180)
    ne_lat: float = Field(..., ge=-90, le=90)
    ne_lng: float = Field(..., ge=-180, le=180)


class ConfidenceScores(BaseModel):
    region_description: float = Field(..., ge=0.0, le=1.0)
    resolution_requirement_m: float = Field(..., ge=0.0, le=1.0)
    time_window_days: float = Field(..., ge=0.0, le=1.0)
    priority: float = Field(..., ge=0.0, le=1.0)


class ParsedIntent(BaseModel):
    region_description: Optional[str] = None
    bounding_box: Optional[BoundingBox] = None
    event_filter: Optional[str] = None
    resolution_requirement_m: Optional[float] = None
    time_window_days: Optional[int] = Field(None, ge=1, le=31)
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    sensor_preference: Optional[str] = None
    confidence: Optional[ConfidenceScores] = None
    uncertainty_notes: List[str] = Field(default_factory=list)


class PlanningRequestCreate(BaseModel):
    raw_input: str = Field(..., min_length=10, max_length=500)
    constellation_id: Optional[str] = None


class PlanningParseResponse(BaseModel):
    status: str
    parsed_intent: ParsedIntent
    confidence: Optional[ConfidenceScores] = None


class PlannedTaskOut(BaseModel):
    id: str
    satellite_id: str
    satellite_name: Optional[str] = None
    target_area: Dict[str, Any]
    event_window: Dict[str, Any]
    resource_allocation: Dict[str, Any]
    solver_status: str
    validator_status: str
    priority_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class PlanningRequestOut(BaseModel):
    id: str
    constellation_id: str
    raw_input: str
    parsed_intent: Optional[Dict[str, Any]] = None
    status: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    tasks: List[PlannedTaskOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ValidationResult(BaseModel):
    passed: bool
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


# ── Replan ─────────────────────────────────────────────────────────────────────


class ReplanRequest(BaseModel):
    priority_override: Optional[str] = Field(None, pattern="^(low|normal|high|urgent)$")
    satellite_id: Optional[str] = Field(None, description="Preferred satellite UUID")
    time_horizon_hours: Optional[int] = Field(24, ge=1, le=168)


class ReplanResponse(BaseModel):
    tasks: List[PlannedTaskOut]
    changes: str
    validation: Optional[ValidationResult] = None
