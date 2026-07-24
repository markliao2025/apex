"""Organization and constellation API schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.satellite import SatelliteOut


class OrganizationOut(BaseModel):
    id: str
    slug: str
    name: str
    role: Literal["owner", "operator", "viewer"]


class ConstellationCreate(BaseModel):
    organization_id: str
    name: str = Field(..., min_length=1, max_length=160)
    slug: str = Field(
        ..., min_length=1, max_length=80, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    description: str | None = Field(None, max_length=2000)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return value.lower()


class ConstellationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=160)
    description: str | None = Field(None, max_length=2000)


class ConstellationOut(BaseModel):
    id: str
    organization_id: str
    slug: str
    name: str
    description: str | None
    is_demo: bool
    role: Literal["owner", "operator", "viewer"]
    satellite_count: int = 0
    created_at: datetime
    updated_at: datetime


class ConstellationSatelliteCreate(BaseModel):
    satellite_id: str
    display_name: str | None = Field(None, max_length=160)


class ConstellationSatelliteOut(BaseModel):
    constellation_id: str
    display_name: str | None
    enabled: bool
    satellite: SatelliteOut
