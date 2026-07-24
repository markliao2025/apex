"""Type definitions for the CP-SAT satellite task scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ImagingWindowData:
    """Data for a single imaging window."""

    aos: datetime
    los: datetime
    max_elevation_deg: float
    illumination_pct: float
    duration_seconds: float
    power_draw: float = 1.0  # Estimated power consumption (arbitrary units)
    data_mb: float = 100.0  # Estimated data volume (MB)


@dataclass
class RequestData:
    """Data for a single planning request."""

    id: str
    priority_score: float = 1.0
    parsed_intent: dict[str, Any] = field(default_factory=dict)


@dataclass
class SatelliteData:
    """Data for a single satellite."""

    id: str
    name: str
    battery_capacity: float = 1000.0  # Battery capacity units
    storage_capacity: float = 50000.0  # Storage capacity (MB)


@dataclass
class SolverInput:
    """Complete input for the CP-SAT solver."""

    requests: list[RequestData]
    satellites: list[SatelliteData]
    imaging_windows: dict[str, list[ImagingWindowData]]
    # Convenience maps
    satellite_ids: list[str] = field(default_factory=list)
    satellite_batteries: dict[str, float] = field(default_factory=dict)
    satellite_storages: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.satellite_ids = [s.id for s in self.satellites]
        self.satellite_batteries = {s.id: s.battery_capacity for s in self.satellites}
        self.satellite_storages = {s.id: s.storage_capacity for s in self.satellites}


@dataclass
class Assignment:
    """A single assignment result from the solver."""

    request_id: str
    satellite_id: str
    window_idx: int


@dataclass
class SolverResult:
    """Output from the CP-SAT solver."""

    status: str  # "optimal", "suboptimal", "infeasible", "model_invalid"
    assignments: list[Assignment]
    objective_value: float = 0.0
    solve_time_ms: float = 0.0
