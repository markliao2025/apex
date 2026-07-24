"""Types for orbit engine calculations."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class OverpassWindow:
    """A single ground-station visibility window for a satellite."""

    aos: datetime
    los: datetime
    max_elevation_deg: float
    duration_seconds: float
    satellite_id: str
    ground_station_id: Optional[str] = None


@dataclass
class ImagingWindow:
    """A single time window when a satellite can image a target area."""

    aos: datetime
    los: datetime
    max_elevation_deg: float
    illumination_pct: float
    duration_seconds: float
    satellite_id: str
    target_bbox: Optional[Dict[str, Any]] = None


@dataclass
class GroundTrackPoint:
    """A single point on a satellite's ground track."""

    timestamp: datetime
    latitude: float
    longitude: float
    altitude_km: float
