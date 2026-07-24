"""Planning API endpoints for Apex — parse, create, get, cancel, replan.

Implements the full satellite task planning workflow:
  POST /parse    — Parse natural language → ParsedIntent
  POST /requests — Create and schedule a planning request
  GET  /requests/{id} — Get request status and results
  POST /requests/{id}/cancel — Cancel a planning request
  POST /requests/{id}/replan — Emergency replanning
"""

import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response

from app.api.dependencies import CurrentUser, DbSession
from app.core.database import SessionLocal
from app.core.errors import AppError
from app.models import (
    ConstellationSatellite,
    PlanningRequest,
    Satellite,
)
from app.planning.intent_parser import get_intent_parser
from app.schemas.planning import (
    PlanningRequestCreate,
    PlanningParseResponse,
    PlannedTaskOut,
    PlanningRequestOut,
    ReplanRequest,
    ReplanResponse,
)
from app.schemas.common import ErrorResponse
from app.services.planning_jobs import run_planning_job
from app.services.tenancy import constellation_access, resolve_constellation

router = APIRouter(tags=["Planning (Apex)"])


# ── Helper functions ──────────────────────────────────────────────────────────


def _orm_to_request_out(req: PlanningRequest) -> PlanningRequestOut:
    """Convert ORM PlanningRequest to response schema."""
    tasks = [
        PlannedTaskOut(
            id=str(t.id),
            satellite_id=str(t.satellite_id),
            satellite_name=t.satellite.name if t.satellite else None,
            target_area=t.target_area,
            event_window=t.event_window,
            resource_allocation=t.resource_allocation,
            solver_status=t.solver_status,
            validator_status=t.validator_status,
            priority_score=t.priority_score or 0.0,
            created_at=t.created_at,
        )
        for t in req.tasks
    ]
    return PlanningRequestOut(
        id=str(req.id),
        constellation_id=str(req.constellation_id),
        raw_input=req.raw_input,
        parsed_intent=req.parsed_intent,
        status=req.status,
        error_code=req.error_code,
        error_message=req.error_message,
        tasks=tasks,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


# ── POST /parse ───────────────────────────────────────────────────────────────


@router.post(
    "/parse",
    response_model=PlanningParseResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
    },
)
async def parse_request(
    body: PlanningRequestCreate,
    current_user: CurrentUser,
    db: DbSession,
    response: Response,
) -> PlanningParseResponse:
    """Parse a natural language planning request into structured intent.

    This is a stateless endpoint — it does not create a PlanningRequest record.
    Use POST /requests to schedule the plan.
    """
    if len(body.raw_input) < 10:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_INPUT",
                "message": "Input too short, need at least 10 characters",
            },
        )

    constellation, _role, deprecated_fallback = resolve_constellation(
        db, current_user, body.constellation_id
    )
    if deprecated_fallback:
        response.headers["Deprecation"] = "true"
        response.headers["Link"] = '</docs#constellation-scope>; rel="deprecation"'

    satellites = (
        db.query(Satellite)
        .join(
            ConstellationSatellite,
            ConstellationSatellite.satellite_id == Satellite.id,
        )
        .filter(
            ConstellationSatellite.constellation_id == constellation.id,
            ConstellationSatellite.enabled.is_(True),
        )
        .all()
    )
    sat_list = [
        {
            "id": str(s.id),
            "name": s.name,
            "payload_type": s.payload_type,
            "max_resolution_m": s.max_resolution_m,
        }
        for s in satellites
    ]

    parser = get_intent_parser()
    intent = parser.parse(body.raw_input, sat_list)

    return PlanningParseResponse(
        status="parsed",
        parsed_intent=intent.to_dict(),
        confidence=intent.confidence.to_dict() if intent.confidence else None,
    )


# ── POST /requests ───────────────────────────────────────────────────────────


@router.post(
    "/requests",
    response_model=PlanningRequestOut,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
    },
)
async def create_request(
    body: PlanningRequestCreate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
    response: Response,
) -> PlanningRequestOut:
    """Create a planning request and schedule it in the background.

    The pipeline runs asynchronously:
    1. Parse intent
    2. Calculate imaging windows
    3. Run CP-SAT solver
    4. Validate tasks
    5. Update request status in DB
    """
    if len(body.raw_input) < 10:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_INPUT", "message": "Input too short"},
        )

    constellation, _role, deprecated_fallback = resolve_constellation(
        db, current_user, body.constellation_id
    )
    if deprecated_fallback:
        response.headers["Deprecation"] = "true"
        response.headers["Link"] = '</docs#constellation-scope>; rel="deprecation"'

    eligible_count = (
        db.query(ConstellationSatellite)
        .filter(
            ConstellationSatellite.constellation_id == constellation.id,
            ConstellationSatellite.enabled.is_(True),
        )
        .count()
    )
    if eligible_count == 0:
        raise AppError(
            "PLANNING_NO_ELIGIBLE_ASSETS",
            "The selected constellation has no enabled satellites.",
            status_code=422,
        )

    request_id = str(uuid.uuid4())
    req = PlanningRequest(
        id=uuid.UUID(request_id),
        user_id=current_user.id,
        constellation_id=constellation.id,
        raw_input=body.raw_input,
        parsed_intent=None,
        status="planning",
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    raw_input = body.raw_input
    constellation_id = constellation.id
    trace_id = request.state.trace_id

    background_tasks.add_task(
        run_planning_job,
        session_factory=SessionLocal,
        request_id=uuid.UUID(request_id),
        raw_input=raw_input,
        constellation_id=constellation_id,
        trace_id=trace_id,
        replace_existing_tasks=False,
    )

    return _orm_to_request_out(req)


# ── GET /requests/{id} ───────────────────────────────────────────────────────


@router.get(
    "/requests/{request_id}",
    response_model=PlanningRequestOut,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def get_request(
    request_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> PlanningRequestOut:
    """Get the status and results of a planning request."""
    try:
        req_uuid = uuid.UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid request ID")

    req = (
        db.query(PlanningRequest)
        .filter(
            PlanningRequest.id == req_uuid,
            PlanningRequest.user_id == current_user.id,
        )
        .first()
    )

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    return _orm_to_request_out(req)


# ── POST /requests/{id}/cancel ───────────────────────────────────────────────


@router.post(
    "/requests/{request_id}/cancel",
    response_model=dict,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def cancel_request(
    request_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """Cancel a planning request."""
    try:
        req_uuid = uuid.UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid request ID")

    req = (
        db.query(PlanningRequest)
        .filter(
            PlanningRequest.id == req_uuid,
            PlanningRequest.user_id == current_user.id,
        )
        .first()
    )

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.status in ("cancelled", "deployed"):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "INVALID_STATE",
                "message": f"Cannot cancel request in '{req.status}' state",
            },
        )

    req.status = "cancelled"
    db.commit()

    return {"status": "cancelled", "request_id": str(req.id)}


# ── POST /requests/{id}/replan ───────────────────────────────────────────────


@router.post(
    "/requests/{request_id}/replan",
    response_model=ReplanResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def replan_request(
    request_id: str,
    body: ReplanRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
) -> ReplanResponse:
    """Emergency replanning with priority override.

    Re-runs the solver with updated constraints:
    - priority_override: override task priority
    - satellite_id: optionally restrict assignment to a specific satellite
    - time_horizon_hours: extend/shorten planning horizon
    """
    try:
        req_uuid = uuid.UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid request ID")

    req = (
        db.query(PlanningRequest)
        .filter(
            PlanningRequest.id == req_uuid,
            PlanningRequest.user_id == current_user.id,
        )
        .first()
    )

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.status == "cancelled":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "INVALID_STATE",
                "message": "Cannot replan a cancelled request",
            },
        )

    if req.status == "planning":
        raise AppError(
            "PLANNING_ALREADY_RUNNING",
            "This planning request is already running.",
            status_code=409,
        )

    constellation_access(db, current_user, req.constellation_id)

    # Capture immutable values before handing work to the background task.
    raw_input = req.raw_input
    constellation_id = req.constellation_id
    preferred_satellite_id = body.satellite_id
    priority_override = body.priority_override
    time_horizon_hours = body.time_horizon_hours
    trace_id = request.state.trace_id
    if preferred_satellite_id:
        try:
            preferred_uuid = uuid.UUID(preferred_satellite_id)
        except ValueError as exc:
            raise AppError(
                "SATELLITE_NOT_FOUND", "Preferred satellite not found.", status_code=404
            ) from exc
        is_member = (
            db.query(ConstellationSatellite)
            .filter(
                ConstellationSatellite.constellation_id == constellation_id,
                ConstellationSatellite.satellite_id == preferred_uuid,
                ConstellationSatellite.enabled.is_(True),
            )
            .first()
        )
        if is_member is None:
            raise AppError(
                "CONSTELLATION_FORBIDDEN",
                "Preferred satellite is not available in this constellation.",
                status_code=403,
            )

    transitioned = (
        db.query(PlanningRequest)
        .filter(
            PlanningRequest.id == req_uuid,
            PlanningRequest.user_id == current_user.id,
            PlanningRequest.status.notin_(["planning", "cancelled"]),
        )
        .update(
            {
                PlanningRequest.status: "planning",
                PlanningRequest.error_code: None,
                PlanningRequest.error_message: None,
            },
            synchronize_session=False,
        )
    )
    if transitioned != 1:
        db.rollback()
        raise AppError(
            "PLANNING_ALREADY_RUNNING",
            "This planning request is already running or was cancelled.",
            status_code=409,
        )
    db.commit()

    background_tasks.add_task(
        run_planning_job,
        session_factory=SessionLocal,
        request_id=req_uuid,
        raw_input=raw_input,
        constellation_id=constellation_id,
        trace_id=trace_id,
        replace_existing_tasks=True,
        preferred_satellite_id=preferred_satellite_id,
        priority_override=priority_override,
        time_horizon_hours=time_horizon_hours,
    )

    # Return immediate response
    return ReplanResponse(
        tasks=[],  # Will be populated after async completion
        changes=f"Replanning request {request_id} with priority={priority_override or 'current'}",
    )
