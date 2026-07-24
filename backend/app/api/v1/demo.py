"""Zero-credential synthetic demo session, replay, impact, and export APIs."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from app.api.dependencies import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import create_access_token, create_refresh_token
from app.models import ConstellationSatellite, User
from app.planning.impact import evaluate_planning_impact
from app.schemas.demo import ReplayCreate, UnavailableWindowInput
from app.scripts.bootstrap_demo import (
    DEMO_CONSTELLATION_ID,
    DEMO_EMAIL,
    DEMO_USER_ID,
)
from app.services.demo_replay import FIXTURE_ID, build_replay, require_replay
from app.services.tenancy import constellation_access

router = APIRouter(prefix="/demo", tags=["Synthetic Demo"])


def _require_demo_enabled() -> None:
    settings = get_settings()
    if not (
        settings.APP_ENV == "demo"
        and settings.DEMO_MODE
        and settings.CONJUNCTION_DEMO_ENABLED
    ):
        raise AppError("NOT_FOUND", "Not found.", status_code=404)


def _require_demo_user(user: User) -> None:
    if user.id != DEMO_USER_ID:
        raise AppError(
            "CONSTELLATION_FORBIDDEN",
            "The synthetic replay requires a demo session.",
            status_code=403,
        )


@router.get("/status")
async def demo_status(db: DbSession) -> dict:
    _require_demo_enabled()
    user_ready = db.query(User).filter(User.id == DEMO_USER_ID).first() is not None
    satellite_count = (
        db.query(ConstellationSatellite)
        .filter(ConstellationSatellite.constellation_id == DEMO_CONSTELLATION_ID)
        .count()
    )
    replay = build_replay()
    return {
        "status": "ready" if user_ready and satellite_count else "not_ready",
        "version": "0.0.1",
        "fixture_id": FIXTURE_ID,
        "fixture_sha256": replay["fixture_sha256"],
        "demo_user_id": str(DEMO_USER_ID),
        "demo_constellation_id": str(DEMO_CONSTELLATION_ID),
        "satellite_count": satellite_count,
    }


@router.post("/session")
async def demo_session(db: DbSession) -> dict:
    _require_demo_enabled()
    user = db.query(User).filter(User.id == DEMO_USER_ID).first()
    if user is None:
        raise AppError(
            "DEMO_BOOTSTRAP_FAILED",
            "The demo account is not ready. Check bootstrap logs.",
            status_code=503,
            retryable=True,
        )
    return {
        "access_token": create_access_token({"sub": str(user.id)}),
        "refresh_token": create_refresh_token({"sub": str(user.id)}),
        "user": {
            "id": str(user.id),
            "email": DEMO_EMAIL,
            "name": user.name,
            "plan": user.plan,
            "created_at": user.created_at,
        },
    }


@router.post("/replays")
async def create_replay(body: ReplayCreate, current_user: CurrentUser) -> dict:
    _require_demo_enabled()
    _require_demo_user(current_user)
    return build_replay()


@router.post("/replays/{replay_id}/planning-impact")
async def planning_impact(
    replay_id: str,
    body: UnavailableWindowInput,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    _require_demo_enabled()
    _require_demo_user(current_user)
    require_replay(replay_id)
    constellation, _role = constellation_access(db, current_user, body.constellation_id)
    try:
        satellite_id = uuid.UUID(body.satellite_id)
    except ValueError as exc:
        raise AppError(
            "CONSTELLATION_FORBIDDEN",
            "Satellite is not available in this constellation.",
            status_code=403,
        ) from exc
    link = (
        db.query(ConstellationSatellite)
        .filter(
            ConstellationSatellite.constellation_id == constellation.id,
            ConstellationSatellite.satellite_id == satellite_id,
        )
        .first()
    )
    if link is None or not link.enabled:
        raise AppError(
            "CONSTELLATION_FORBIDDEN",
            "Satellite is not available in this constellation.",
            status_code=403,
        )
    return evaluate_planning_impact(body)


@router.get("/replays/{replay_id}/export")
async def export_replay(
    replay_id: str,
    current_user: CurrentUser,
    format: str = "json",
) -> Response:
    _require_demo_enabled()
    _require_demo_user(current_user)
    replay = require_replay(replay_id)
    if format == "json":
        return JSONResponse(
            replay,
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{replay["event_id"].lower()}-evidence.json"'
                )
            },
        )
    if format == "md":
        markdown = "\n".join(
            [
                f"# {replay['event_id']} evidence",
                "",
                (
                    "> Research and decision-support software. Not flight-certified. "
                    "No maneuver is executed by Apex."
                ),
                "> Synthetic demonstration — not for operational decisions.",
                "",
                f"- Replay ID: `{replay['replay_id']}`",
                f"- Fixture SHA-256: `{replay['fixture_sha256']}`",
                f"- TCA: {replay['tca_utc']}",
                f"- Miss distance: {replay['relative_state']['miss_distance_m']} m",
                (
                    "- Provided Pc: "
                    f"{replay['risk']['collision_probability']} "
                    "(Apex did not compute it)"
                ),
                "- Covariance: unavailable; Pc is not independently reproducible",
                "",
                "## Limitations",
                "",
                *[f"- {item}" for item in replay["limitations"]],
            ]
        )
        return PlainTextResponse(
            markdown,
            media_type="text/markdown",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{replay["event_id"].lower()}-evidence.md"'
                )
            },
        )
    raise AppError(
        "EVENT_INPUT_INVALID",
        "Export format must be json or md.",
        status_code=422,
    )
