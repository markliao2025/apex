"""Deterministic hypothetical planning impact for the Phase 0 demo."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.planning.solver import solve
from app.planning.solver_types import (
    ImagingWindowData,
    RequestData,
    SatelliteData,
    SolverInput,
)
from app.schemas.demo import UnavailableWindowInput

ALGORITHM_VERSION = "apex.planning-impact.v1"


def _task_id(request_id: str, satellite_id: str, start: str) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL, f"apex-impact:{request_id}:{satellite_id}:{start}"
        )
    )


def evaluate_planning_impact(window: UnavailableWindowInput) -> dict:
    """Compare one fixed synthetic opportunity before/after a hypothetical outage."""
    opportunity_start = datetime(2024, 6, 1, 11, 58, tzinfo=timezone.utc)
    opportunity_end = opportunity_start + timedelta(minutes=4)
    overlaps_opportunity = (
        window.unavailable_from_utc < opportunity_end
        and opportunity_start < window.unavailable_to_utc
    )
    request_id = "apex-impact-request-001"
    imaging_window = ImagingWindowData(
        aos=opportunity_start,
        los=opportunity_end,
        max_elevation_deg=45.0,
        illumination_pct=0.8,
        duration_seconds=240.0,
        power_draw=1.0,
        data_mb=100.0,
    )
    satellite = SatelliteData(
        id=window.satellite_id,
        name="Selected constellation satellite",
        battery_capacity=100.0,
        storage_capacity=1000.0,
    )
    before_input = SolverInput(
        requests=[RequestData(id=request_id, priority_score=1.0)],
        satellites=[satellite],
        imaging_windows={window.satellite_id: [imaging_window]},
    )
    after_input = SolverInput(
        requests=[RequestData(id=request_id, priority_score=1.0)],
        satellites=[satellite],
        imaging_windows={
            window.satellite_id: [] if overlaps_opportunity else [imaging_window]
        },
    )
    before = solve(before_input)
    after = solve(after_input)

    before_ids = [
        _task_id(request_id, assignment.satellite_id, opportunity_start.isoformat())
        for assignment in before.assignments
    ]
    after_ids = [
        _task_id(request_id, assignment.satellite_id, opportunity_start.isoformat())
        for assignment in after.assignments
    ]
    evidence: dict[str, Any] = {
        "schema_version": "apex.demo.planning-impact.v1",
        "algorithm_version": ALGORITHM_VERSION,
        "evaluation_time_utc": "2024-05-31T12:00:00Z",
        "hypothesis": {
            "kind": "satellite_unavailable_window",
            "satellite_id": window.satellite_id,
            "unavailable_from_utc": window.unavailable_from_utc.isoformat().replace(
                "+00:00", "Z"
            ),
            "unavailable_to_utc": window.unavailable_to_utc.isoformat().replace(
                "+00:00", "Z"
            ),
            "reason": window.reason,
            "overlaps_synthetic_opportunity": overlaps_opportunity,
            "filter_reason": (
                "hypothetical_satellite_unavailable" if overlaps_opportunity else None
            ),
        },
        "before": {
            "task_count": len(before.assignments),
            "task_ids": before_ids,
            "objective_value": before.objective_value,
            "solver_status": before.status,
        },
        "after": {
            "task_count": len(after.assignments),
            "task_ids": after_ids,
            "objective_value": after.objective_value,
            "solver_status": after.status,
        },
        "diff": {
            "retained_task_ids": sorted(set(before_ids) & set(after_ids)),
            "removed_task_ids": sorted(set(before_ids) - set(after_ids)),
            "reassigned_task_ids": [],
            "objective_delta": after.objective_value - before.objective_value,
            "affected_window": {
                "start_utc": opportunity_start.isoformat().replace("+00:00", "Z"),
                "end_utc": opportunity_end.isoformat().replace("+00:00", "Z"),
            },
        },
        "physics_verified": False,
        "limitations": [
            (
                "Research and decision-support software. Not flight-certified. "
                "No maneuver is executed by Apex."
            ),
            "This is a hypothetical availability scenario, not a maneuver recommendation.",
            "The opportunity is synthetic and does not predict a real orbit trajectory.",
            "Collision probability is not recomputed.",
        ],
    }
    evidence_sha256 = hashlib.sha256(
        json.dumps(
            evidence,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()
    ).hexdigest()

    # Runtime metrics are deliberately outside the evidence hash: solver duration is
    # diagnostic data and varies by machine, while the semantic result must replay.
    evidence["evidence_sha256"] = evidence_sha256
    evidence["before"]["solve_time_ms"] = before.solve_time_ms
    evidence["after"]["solve_time_ms"] = after.solve_time_ms
    return evidence
