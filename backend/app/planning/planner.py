"""Planner — assembles the full satellite task planning pipeline.

Orchestrates: Intent Parser → Geocoder → Imaging Windows → CP-SAT Solver → Validator

Returns a PlanningResult with scheduled tasks, validation status, and
human-readable explanations.

Pipeline:
  1. Parse natural language request → ParsedIntent
  2. Geocode region description → BoundingBox
  3. Calculate imaging windows for each eligible satellite
  4. Run CP-SAT solver to assign tasks to windows
  5. Validate each assignment against physical constraints
  6. Return final schedule with status and details
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models import ConstellationSatellite, Satellite
from app.planning.geocoding import geocode_region
from app.planning.intent import ParsedIntent
from app.planning.intent_parser import get_intent_parser
from app.planning.solver import solve
from app.planning.solver_types import (
    ImagingWindowData,
    RequestData,
    SatelliteData,
    SolverInput,
)
from app.planning.validator import run_validator, validate_task


class PlanningError(Exception):
    """Raised when the planning pipeline fails."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


@dataclass(frozen=True)
class UnavailableWindow:
    """A hypothetical satellite outage; it is not a maneuver result."""

    satellite_id: str
    unavailable_from_utc: datetime
    unavailable_to_utc: datetime
    reason: str

    def __post_init__(self) -> None:
        if (
            self.unavailable_from_utc.tzinfo is None
            or self.unavailable_to_utc.tzinfo is None
        ):
            raise ValueError("Unavailable window timestamps must be timezone-aware")
        if self.unavailable_from_utc >= self.unavailable_to_utc:
            raise ValueError("Unavailable window start must be before end")


@dataclass
class PlannedTask:
    """A single planned imaging task."""

    id: str
    request_id: str
    satellite_id: str
    acquisition_start: datetime
    acquisition_end: datetime
    max_elevation_deg: float
    illumination_pct: float
    duration_seconds: float
    power_draw: float
    data_mb: float
    priority_score: float
    validator_status: str
    validator_details: dict
    violations: list[str]
    warnings: list[str]


@dataclass
class PlanningResult:
    """Complete result from the planning pipeline."""

    request_id: str
    status: str  # "ready", "partial", "failed"
    parsed_intent: ParsedIntent
    tasks: list[PlannedTask]
    validation_summary: dict
    explanation: str
    errors: list[str]


def run_planner(
    raw_input: str,
    db: Session,
    planning_horizon_days: int = 7,
    min_elevation_deg: float = 5.0,
    batteries: Optional[dict[str, float]] = None,
    storages: Optional[dict[str, float]] = None,
    constellation_id: uuid.UUID | str | None = None,
    satellite_id: str | None = None,
    evaluation_time_utc: datetime | None = None,
    unavailable_windows: list[UnavailableWindow] | None = None,
    request_id: str | None = None,
    priority_override: str | None = None,
) -> PlanningResult:
    """Execute the full planning pipeline.

    Args:
        raw_input: User's natural-language request.
        db: Database session to query satellites.
        planning_horizon_days: Number of days ahead to search.
        min_elevation_deg: Minimum elevation angle for imaging.
        batteries: Optional override of battery capacities per satellite ID.
        storages: Optional override of storage capacities per satellite ID (MB).

    Returns:
        PlanningResult with scheduled tasks and validation info.
    """
    parser = get_intent_parser()
    request_id = request_id or str(uuid.uuid4())
    errors: list[str] = []

    # ── Step 1: Parse intent ──────────────────────────────────────────────────
    intent = parser.parse(raw_input)
    if priority_override is not None:
        intent.priority = priority_override

    # ── Step 2: Get eligible satellites ──────────────────────────────────────
    if constellation_id is None:
        raise PlanningError(
            "CONSTELLATION_REQUIRED",
            "Planner execution requires an explicit constellation scope.",
        )
    satellites_query = (
        db.query(Satellite)
        .join(
            ConstellationSatellite,
            ConstellationSatellite.satellite_id == Satellite.id,
        )
        .filter(
            ConstellationSatellite.constellation_id == constellation_id,
            ConstellationSatellite.enabled.is_(True),
        )
    )
    if satellite_id:
        try:
            preferred_satellite_id = uuid.UUID(satellite_id)
        except ValueError as exc:
            raise PlanningError(
                "SATELLITE_NOT_FOUND", "Preferred satellite ID is invalid."
            ) from exc
        satellites_query = satellites_query.filter(
            Satellite.id == preferred_satellite_id
        )
    satellites = satellites_query.order_by(Satellite.norad_id).all()
    if not satellites:
        return PlanningResult(
            request_id=request_id,
            status="failed",
            parsed_intent=intent,
            tasks=[],
            validation_summary={"total": 0, "passed": 0, "failed": 0},
            explanation="No satellites available in the database. Please seed satellite data first.",
            errors=["no_satellites"],
        )

    # Filter satellites by sensor preference if specified
    if intent.sensor_preference:
        payload_map = {
            "optical": ["eo_optical"],
            "multispectral": ["eo_multispectral"],
            "sar": ["sar"],
            "hyperspectral": ["eo_multispectral"],
        }
        allowed_payloads = payload_map.get(intent.sensor_preference, ["eo_optical"])
        satellites = [s for s in satellites if s.payload_type in allowed_payloads]

    # Filter by resolution requirement
    if intent.resolution_requirement_m:
        satellites = [
            s
            for s in satellites
            if s.max_resolution_m <= intent.resolution_requirement_m
        ]

    if not satellites:
        return PlanningResult(
            request_id=request_id,
            status="failed",
            parsed_intent=intent,
            tasks=[],
            validation_summary={"total": 0, "passed": 0, "failed": 0},
            explanation=(
                f"No satellites meet the criteria: "
                f"sensor={intent.sensor_preference or 'any'}, "
                f"resolution<=({intent.resolution_requirement_m or 'any'}m)."
            ),
            errors=["no_matching_satellites"],
        )

    # ── Step 3: Get imaging windows ───────────────────────────────────────────
    from app.orbit.imaging import calculate_imaging_windows as calc_imaging_windows

    bbox = None
    if intent.bounding_box:
        bbox = {
            "sw_lat": intent.bounding_box.sw_lat,
            "sw_lng": intent.bounding_box.sw_lng,
            "ne_lat": intent.bounding_box.ne_lat,
            "ne_lng": intent.bounding_box.ne_lng,
        }

    if not bbox:
        # Try to geocode from region description
        if intent.region_description:
            geo_bbox = geocode_region(intent.region_description)
            if geo_bbox:
                bbox = geo_bbox.to_dict()
            else:
                errors.append(f"Could not geocode region: {intent.region_description}")

    if not bbox:
        return PlanningResult(
            request_id=request_id,
            status="failed",
            parsed_intent=intent,
            tasks=[],
            validation_summary={"total": 0, "passed": 0, "failed": 0},
            explanation="No bounding box available. Please specify a geographic region in your request.",
            errors=["no_bounding_box"],
        )

    now = evaluation_time_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise PlanningError(
            "EVALUATION_TIME_INVALID", "Evaluation time must be timezone-aware UTC."
        )
    now = now.astimezone(timezone.utc)
    end_time = now + timedelta(days=planning_horizon_days)

    # Collect imaging windows for each satellite
    satellite_windows: dict[str, list[ImagingWindowData]] = {}
    for sat in satellites:
        sat_id = str(sat.id)
        windows_raw = calc_imaging_windows(
            satellite={
                "id": sat_id,
                "tle_line1": sat.tle_line1,
                "tle_line2": sat.tle_line2,
            },
            bbox=bbox,
            start_time=now,
            end_time=end_time,
            min_elevation_deg=max(min_elevation_deg, sat.min_elevation_deg),
        )

        # Convert raw dict windows to ImagingWindowData
        window_list = []
        for w in windows_raw:
            window = ImagingWindowData(
                aos=w["aos"],
                los=w["los"],
                max_elevation_deg=w["max_elevation_deg"],
                illumination_pct=w["illumination_pct"],
                duration_seconds=w["duration_seconds"],
                power_draw=1.0,
                data_mb=100.0,
            )
            blocked = any(
                unavailable.satellite_id == sat_id
                and window.aos < unavailable.unavailable_to_utc
                and unavailable.unavailable_from_utc < window.los
                for unavailable in (unavailable_windows or [])
            )
            if not blocked:
                window_list.append(window)
        if window_list:
            satellite_windows[sat_id] = window_list

    if not satellite_windows:
        return PlanningResult(
            request_id=request_id,
            status="failed",
            parsed_intent=intent,
            tasks=[],
            validation_summary={"total": 0, "passed": 0, "failed": 0},
            explanation="No imaging windows found for any satellite over the target region.",
            errors=["no_imaging_windows"],
        )

    # ── Step 4: Run CP-SAT solver ─────────────────────────────────────────────
    # Build solver input
    priority_map = {
        "low": 0.3,
        "normal": 0.6,
        "high": 0.85,
        "urgent": 1.0,
    }
    priority_score = priority_map.get(intent.priority, 0.6)

    requests = [RequestData(id=request_id, priority_score=priority_score)]
    sat_data_list = [
        SatelliteData(
            id=str(s.id),
            name=s.name,
            battery_capacity=batteries.get(str(s.id), 100.0) if batteries else 100.0,
            storage_capacity=storages.get(str(s.id), 50000.0) if storages else 50000.0,
        )
        for s in satellites
        if str(s.id) in satellite_windows
    ]

    solver_input = SolverInput(
        requests=requests,
        satellites=sat_data_list,
        imaging_windows=satellite_windows,
    )

    solver_result = solve(solver_input)

    if solver_result.status == "infeasible" or not solver_result.assignments:
        return PlanningResult(
            request_id=request_id,
            status="failed",
            parsed_intent=intent,
            tasks=[],
            validation_summary={"total": 0, "passed": 0, "failed": 0},
            explanation="No feasible schedule found. Try relaxing constraints or expanding the time window.",
            errors=["infeasible"],
        )

    # ── Step 5: Validate assignments ──────────────────────────────────────────
    validation_result = run_validator(solver_result, solver_input)

    # ── Step 6: Build final result ────────────────────────────────────────────
    planned_tasks = []
    for assignment in solver_result.assignments:
        windows = satellite_windows.get(assignment.satellite_id, [])
        if assignment.window_idx >= len(windows):
            continue

        window = windows[assignment.window_idx]
        task_validation = validate_task(
            assignment=assignment,
            solver_input=solver_input,
        )

        planned_tasks.append(
            PlannedTask(
                id=str(
                    uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        (
                            f"apex:{request_id}:{assignment.satellite_id}:"
                            f"{window.aos.isoformat()}:{window.los.isoformat()}"
                        ),
                    )
                ),
                request_id=assignment.request_id,
                satellite_id=assignment.satellite_id,
                acquisition_start=window.aos,
                acquisition_end=window.los,
                max_elevation_deg=window.max_elevation_deg,
                illumination_pct=window.illumination_pct,
                duration_seconds=window.duration_seconds,
                power_draw=window.power_draw,
                data_mb=window.data_mb,
                priority_score=priority_score,
                validator_status="passed" if task_validation.passed else "failed",
                validator_details=task_validation.details,
                violations=task_validation.violations,
                warnings=task_validation.warnings,
            )
        )

    # Determine overall status
    if not planned_tasks:
        status = "failed"
    elif all(t.validator_status == "passed" for t in planned_tasks):
        status = "ready"
    else:
        status = "partial"

    explanation = _build_explanation(
        intent=intent,
        total_windows=sum(len(v) for v in satellite_windows.values()),
        total_tasks=len(planned_tasks),
        passed_tasks=validation_result["passed"],
        failed_tasks=validation_result["failed"],
        solver_status=solver_result.status,
    )

    return PlanningResult(
        request_id=request_id,
        status=status,
        parsed_intent=intent,
        tasks=planned_tasks,
        validation_summary=validation_result,
        explanation=explanation,
        errors=errors,
    )


def _build_explanation(
    intent: ParsedIntent,
    total_windows: int,
    total_tasks: int,
    passed_tasks: int,
    failed_tasks: int,
    solver_status: str,
) -> str:
    """Build a human-readable explanation of the planning result."""
    parts = []

    # Region summary
    if intent.region_description:
        parts.append(f"Planning for region: **{intent.region_description}**")

    # Priority and constraints
    if intent.priority != "normal":
        parts.append(f"Priority: **{intent.priority.upper()}**")
    if intent.resolution_requirement_m:
        parts.append(f"Resolution: **≤{intent.resolution_requirement_m}m**")
    if intent.event_filter:
        parts.append(f"Event filter: **{intent.event_filter}**")

    # Results
    parts.append(
        f"Solver status: {solver_status} | Windows: {total_windows} | Tasks: {total_tasks}"
    )
    parts.append(f"Validated: {passed_tasks} passed, {failed_tasks} failed")

    # Recommendations
    if failed_tasks > 0:
        parts.append(
            "⚠️ Some tasks failed validation. Check the violations field "
            "for details and try relaxing constraints."
        )
    if solver_status == "suboptimal":
        parts.append(
            "⏱ Solver found a feasible solution but may not be optimal. "
            "Try extending the time window for better results."
        )

    return " | ".join(parts) if parts else "Planning completed."
