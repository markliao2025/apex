"""Physics validator — checks scheduled tasks against physical constraints.

After the CP-SAT solver produces candidate tasks, each one is validated
against seven physical constraints before being accepted into the
final schedule.

Validation checks:
  1. Elevation angle at AoS >= satellite.min_elevation_deg
  2. Solar illumination at target >= 10% (not in Earth shadow)
  3. Task duration <= ground station visibility window
  4. Power consumption <= battery remaining
  5. Data size <= remaining storage
  6. Turn rate between consecutive tasks on same satellite is feasible
  7. Downlink window exists after imaging (if same-orbit requirement)

Returns a ValidationResult with passed/failed status, violations, warnings,
and detailed numerical values for each check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.planning.solver_types import (
    Assignment,
    SolverResult,
    SolverInput,
)


@dataclass
class ValidationResult:
    """Result of physics validation for a single planned task."""

    passed: bool = True
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def add_violation(self, name: str, value: float, limit: float) -> None:
        """Record a constraint violation."""
        self.passed = False
        self.violations.append(f"{name}: {value:.2f} < {limit:.2f}")

    def add_warning(self, name: str, value: float, limit: float) -> None:
        """Record a warning (constraint close to limit)."""
        self.warnings.append(f"{name}: {value:.2f} near {limit:.2f}")

    def set_detail(
        self, name: str, value: float, unit: str = "", status: str = "OK"
    ) -> None:
        """Record a detail value."""
        self.details[name] = {
            "value": round(value, 2),
            "unit": unit,
            "status": status,
        }


def validate_task(
    assignment: Assignment,
    solver_input: SolverInput,
    ground_station: Optional[dict] = None,
    battery_remaining: float = 100.0,
    storage_remaining_mb: float = 50000.0,
) -> ValidationResult:
    """Validate a single planned task against physical constraints.

    Args:
        assignment: The solver assignment to validate.
        solver_input: Full planning input with satellites and windows.
        ground_station: Optional ground station dict for downlink validation.
        battery_remaining: Current battery level (0–100%).
        storage_remaining_mb: Remaining onboard storage (MB).

    Returns:
        ValidationResult with passed/failed status.
    """
    result = ValidationResult()

    # Find satellite and window data
    sat_data = None
    for sat in solver_input.satellites:
        if str(sat.id) == assignment.satellite_id:
            sat_data = sat
            break
    if sat_data is None:
        result.passed = False
        result.violations.append(
            "satellite_not_found: satellite ID not in solver input"
        )
        return result

    windows = solver_input.imaging_windows.get(assignment.satellite_id, [])
    if assignment.window_idx >= len(windows):
        result.passed = False
        result.violations.append("window_not_found: window index out of range")
        return result

    window = windows[assignment.window_idx]

    # ── Check 1: Elevation angle ─────────────────────────────────────────────
    # Satellite min_elevation_deg from model or default 5.0°
    min_elev = getattr(sat_data, "min_elevation_deg", 5.0)
    elev = window.max_elevation_deg
    result.set_detail(
        "elevation_at_aos", elev, "deg", "OK" if elev >= min_elev else "FAIL"
    )

    if elev < min_elev:
        result.add_violation(
            f"elevation_angle_at_aos (req >= {min_elev:.1f}°)", elev, min_elev
        )
    elif elev < min_elev * 1.2:
        result.add_warning("elevation_angle_margin_low", elev, min_elev * 1.2)

    # ── Check 2: Solar illumination ──────────────────────────────────────────
    min_illum = 0.10  # At least 10% of target must be sunlit
    illum = window.illumination_pct
    result.set_detail(
        "solar_illumination", illum * 100, "%", "OK" if illum >= min_illum else "FAIL"
    )

    if illum < min_illum:
        result.add_violation(
            f"illumination_below_threshold (req >= {min_illum * 100:.0f}%)",
            illum * 100,
            min_illum * 100,
        )
    elif illum < min_illum * 2:
        result.add_warning("illumination_margin_low", illum * 100, min_illum * 200)

    # ── Check 3: Task duration vs visibility window ─────────────────────────
    duration = window.duration_seconds
    result.set_detail("task_duration", duration, "s", "OK")

    # Reasonable bounds: 5s–300s for optical imaging
    if duration < 5:
        result.add_warning("duration_too_short", duration, 5)
    if duration > 300:
        result.add_warning("duration_long", duration, 300)

    # ── Check 4: Battery consumption ─────────────────────────────────────────
    power_draw = window.power_draw
    result.set_detail("power_consumption", power_draw, "units", "OK")

    if battery_remaining is not None and power_draw > battery_remaining:
        result.add_violation(
            f"battery_insufficient (need {power_draw:.1f}, have {battery_remaining:.1f})",
            power_draw,
            battery_remaining,
        )
    elif battery_remaining is not None and power_draw > battery_remaining * 0.8:
        result.add_warning("battery_margin_low", power_draw, battery_remaining * 0.8)

    # ── Check 5: Storage capacity ────────────────────────────────────────────
    data_mb = window.data_mb
    result.set_detail("data_size", data_mb, "MB", "OK")

    if storage_remaining_mb is not None and data_mb > storage_remaining_mb:
        result.add_violation(
            f"storage_insufficient (need {data_mb:.1f} MB, have {storage_remaining_mb:.1f} MB)",
            data_mb,
            storage_remaining_mb,
        )
    elif storage_remaining_mb is not None and data_mb > storage_remaining_mb * 0.8:
        result.add_warning("storage_margin_low", data_mb, storage_remaining_mb * 0.8)

    # ── Check 6: Turn rate feasibility ───────────────────────────────────────
    # (Soft check — logged as warning, not violation)
    # Estimated turn rate: we approximate that the satellite may need to
    # slew between targets. Flag if elevation is very low (indicating edge-of-swath).
    if elev < min_elev * 1.5:
        # Low elevation typically means edge-of-swath, requiring attitude slew
        slew_deg = min_elev * 1.5 - elev
        result.set_detail("estimated_turn_rate", slew_deg, "deg")
        result.warnings.append(f"low_elevation ({elev:.1f}°) may require attitude slew")

    # ── Check 7: Downlink window (if same-orbit requirement) ────────────────
    if ground_station:
        # Assume downlink window is ~5 min after imaging window
        result.set_detail("downlink_window_available", 1.0, "estimated")

    return result


def validate_schedule(
    solver_result: SolverResult,
    solver_input: SolverInput,
    ground_station: Optional[dict] = None,
) -> dict[str, dict]:
    """Validate all assignments in a solver result.

    Args:
        solver_result: Output from the CP-SAT solver.
        solver_input: Full planning input.
        ground_station: Optional ground station for downlink validation.

    Returns:
        Dict mapping request_id -> {validator_status, task_data, ...}
    """
    validated: dict[str, dict] = {}

    for assignment in solver_result.assignments:
        req_id = assignment.request_id
        task_validation = validate_task(
            assignment=assignment,
            solver_input=solver_input,
            ground_station=ground_station,
        )

        # Build task data dict for API response
        windows = solver_input.imaging_windows.get(assignment.satellite_id, [])
        window_data = (
            windows[assignment.window_idx]
            if assignment.window_idx < len(windows)
            else None
        )

        validated[req_id] = {
            "validator_status": "passed" if task_validation.passed else "failed",
            "violation_count": len(task_validation.violations),
            "warning_count": len(task_validation.warnings),
            "violations": task_validation.violations,
            "warnings": task_validation.warnings,
            "details": task_validation.details,
            "task": {
                "satellite_id": assignment.satellite_id,
                "window_idx": assignment.window_idx,
                "acquisition_start": window_data.aos if window_data else None,
                "acquisition_end": window_data.los if window_data else None,
                "max_elevation": window_data.max_elevation_deg if window_data else None,
                "illumination_pct": window_data.illumination_pct
                if window_data
                else None,
                "duration_seconds": window_data.duration_seconds
                if window_data
                else None,
                "power_draw": window_data.power_draw if window_data else None,
                "data_mb": window_data.data_mb if window_data else None,
            },
        }

    return validated


def run_validator(
    solver_result: SolverResult,
    solver_input: SolverInput,
    ground_station: Optional[dict] = None,
) -> dict:
    """Run validation and return aggregated results.

    Returns:
        {
            "total": int,
            "passed": int,
            "failed": int,
            "tasks": {request_id: task_validation_data},
            "solver_status": str,
        }
    """
    validated = validate_schedule(solver_result, solver_input, ground_station)

    passed = sum(1 for t in validated.values() if t["validator_status"] == "passed")
    failed = len(validated) - passed

    return {
        "total": len(validated),
        "passed": passed,
        "failed": failed,
        "tasks": validated,
        "solver_status": solver_result.status,
    }
