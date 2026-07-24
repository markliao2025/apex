"""Satellite-related Pydantic schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class SatelliteCreate(BaseModel):
    norad_id: str
    name: str = Field(..., max_length=200)
    tle_line1: str = Field(..., max_length=70)
    tle_line2: str = Field(..., max_length=70)
    tle_epoch: datetime
    orbit_type: str
    altitude_km_min: float
    altitude_km_max: float
    inclination_deg: float
    eccentricity: float
    payload_type: str
    max_resolution_m: float
    swath_width_km: float
    max_storage_gb: float
    max_power_w: float


class SatelliteOut(BaseModel):
    id: str
    norad_id: str
    name: str
    tle_epoch: datetime
    orbit_type: str
    payload_type: str
    max_resolution_m: float
    swath_width_km: float

    model_config = {"from_attributes": True}


class OverpassWindow(BaseModel):
    aos: datetime
    los: datetime
    max_elevation: float
    duration_seconds: float


class GroundTrackPoint(BaseModel):
    timestamp: datetime
    latitude: float
    longitude: float
    altitude_km: float
