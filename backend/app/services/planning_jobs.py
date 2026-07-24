"""Testable background jobs for the constellation-scoped planning pipeline."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.models import PlanningRequest, PlannedTask as PlannedTaskModel
from app.planning.planner import PlanningResult, run_planner

logger = logging.getLogger("apex.planning")

SessionFactory = Callable[[], Session]
Planner = Callable[..., PlanningResult]
PUBLIC_FAILURE_MESSAGE = (
    "Planning failed. Review server logs using the request identifier."
)


def _planned_task(
    request_id: uuid.UUID,
    result: PlanningResult,
    task,
) -> PlannedTaskModel:
    bounding_box = result.parsed_intent.bounding_box
    return PlannedTaskModel(
        id=uuid.UUID(task.id),
        planning_request_id=request_id,
        satellite_id=uuid.UUID(task.satellite_id),
        target_area={
            "type": "Polygon",
            "coordinates": [
                [
                    bounding_box.sw_lng if bounding_box else 0,
                    bounding_box.sw_lat if bounding_box else 0,
                ],
                [
                    bounding_box.ne_lng if bounding_box else 0,
                    bounding_box.ne_lat if bounding_box else 0,
                ],
            ],
        },
        event_window={
            "aos_time": task.acquisition_start.isoformat(),
            "los_time": task.acquisition_end.isoformat(),
            "max_elevation_deg": task.max_elevation_deg,
        },
        resource_allocation={
            "power_w": task.power_draw,
            "storage_mb": task.data_mb,
            "battery_delta_percent": task.power_draw * 0.02,
        },
        solver_status="optimal",
        validator_status=task.validator_status,
        failure_reason="; ".join(task.violations) if task.violations else None,
        priority_score=task.priority_score,
    )


def _mark_failed(
    session_factory: SessionFactory,
    *,
    request_id: uuid.UUID,
    error_code: str,
) -> None:
    with session_factory() as error_db:
        failed_request = (
            error_db.query(PlanningRequest)
            .filter(PlanningRequest.id == request_id)
            .with_for_update()
            .first()
        )
        if failed_request and failed_request.status == "planning":
            failed_request.status = "planning_error"
            failed_request.error_code = error_code
            failed_request.error_message = PUBLIC_FAILURE_MESSAGE
            error_db.commit()


def run_planning_job(
    *,
    session_factory: SessionFactory,
    request_id: uuid.UUID,
    raw_input: str,
    constellation_id: uuid.UUID,
    trace_id: str,
    replace_existing_tasks: bool,
    preferred_satellite_id: str | None = None,
    priority_override: str | None = None,
    time_horizon_hours: int | None = None,
    planner: Planner = run_planner,
) -> str:
    """Run planning and atomically persist it unless the request was cancelled."""
    error_code = (
        "PLANNING_REPLAN_ERROR" if replace_existing_tasks else "PLANNING_PIPELINE_ERROR"
    )
    horizon_days = max(1, (time_horizon_hours + 23) // 24) if time_horizon_hours else 7

    try:
        with session_factory() as job_db:
            result = planner(
                raw_input=raw_input,
                db=job_db,
                constellation_id=constellation_id,
                satellite_id=preferred_satellite_id,
                priority_override=priority_override,
                planning_horizon_days=horizon_days,
                min_elevation_deg=5.0,
                request_id=str(request_id),
            )
            db_request = (
                job_db.query(PlanningRequest)
                .filter(PlanningRequest.id == request_id)
                .with_for_update()
                .first()
            )
            if db_request is None:
                job_db.rollback()
                return "not_found"
            if db_request.status == "cancelled":
                job_db.rollback()
                return "cancelled"

            if replace_existing_tasks:
                for existing_task in list(db_request.tasks):
                    job_db.delete(existing_task)

            for task in result.tasks:
                job_db.add(_planned_task(request_id, result, task))

            db_request.parsed_intent = result.parsed_intent.to_dict()
            db_request.status = result.status
            db_request.error_code = None
            db_request.error_message = None
            job_db.commit()
            return "completed"
    except Exception:
        logger.exception(
            "planning_job_failed trace_id=%s request_id=%s error_code=%s",
            trace_id,
            request_id,
            error_code,
        )
        _mark_failed(
            session_factory,
            request_id=request_id,
            error_code=error_code,
        )
        return "failed"
