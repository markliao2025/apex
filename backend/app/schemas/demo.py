"""Strict schemas for the synthetic Phase 0 conjunction replay."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictDemoModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Provenance(StrictDemoModel):
    kind: Literal["synthetic"]
    license: Literal["CC0-1.0"]
    created_by: str
    source_url: str | None


class SpaceObjectRef(StrictDemoModel):
    catalog_id: str = Field(..., pattern=r"^\d{6,}$")
    name: str


class RelativeState(StrictDemoModel):
    miss_distance_m: float = Field(..., ge=0)
    relative_speed_m_s: float = Field(..., gt=0)


class ProvidedRisk(StrictDemoModel):
    collision_probability: float = Field(..., ge=0, le=1)
    source: Literal["provided"]
    method: Literal["synthetic_demo_value"]


class CovarianceStatus(StrictDemoModel):
    available: Literal[False]
    reference_frame: None = None


class ConjunctionEvent(StrictDemoModel):
    schema_version: Literal["apex.demo.conjunction.v1"]
    event_id: Literal["APEX-SYNTHETIC-001"]
    provenance: Provenance
    created_at_utc: datetime
    tca_utc: datetime
    primary: SpaceObjectRef
    secondary: SpaceObjectRef
    relative_state: RelativeState
    risk: ProvidedRisk
    covariance: CovarianceStatus
    limitations: list[str] = Field(..., min_length=1)

    @field_validator("created_at_utc", "tca_utc", mode="before")
    @classmethod
    def require_zulu(cls, value):
        if not isinstance(value, str) or not value.endswith("Z"):
            raise ValueError("timestamp must use explicit Zulu UTC")
        return value

    @model_validator(mode="after")
    def validate_time_order(self) -> "ConjunctionEvent":
        if self.tca_utc <= self.created_at_utc:
            raise ValueError("tca_utc must be later than created_at_utc")
        return self


class ReplayCreate(StrictDemoModel):
    fixture_id: Literal["apex-synthetic-001"] = "apex-synthetic-001"


class UnavailableWindowInput(StrictDemoModel):
    constellation_id: str
    satellite_id: str
    unavailable_from_utc: datetime
    unavailable_to_utc: datetime
    reason: Literal["synthetic_conjunction_what_if"]

    @field_validator("unavailable_from_utc", "unavailable_to_utc", mode="before")
    @classmethod
    def require_zulu(cls, value):
        if not isinstance(value, str) or not value.endswith("Z"):
            raise ValueError("timestamp must use explicit Zulu UTC")
        return value

    @model_validator(mode="after")
    def validate_window(self) -> "UnavailableWindowInput":
        if self.unavailable_from_utc >= self.unavailable_to_utc:
            raise ValueError("unavailable_from_utc must be before unavailable_to_utc")
        return self
