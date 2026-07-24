"""Orbit engine HTTP endpoints — imaging windows and overpass calculations."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import CurrentUser, DbSession
from app.core.errors import AppError
from app.models import ConstellationSatellite, GroundStation, Satellite
from app.orbit.propagation import calculate_overpass_windows
from app.orbit.imaging import calculate_imaging_windows
from app.schemas.common import ErrorResponse
from app.services.tenancy import resolve_constellation

router = APIRouter(tags=["Orbit Engine"])


class ImagingWindowRequest(BaseModel):
    satellite_id: str = Field(..., description="Satellite UUID")
    constellation_id: str | None = None
    bbox: dict = Field(
        ..., description="Bounding box with sw_lat, sw_lng, ne_lat, ne_lng"
    )
    min_elevation_deg: float = Field(5.0, ge=0, le=90)
    max_sun_angle_deg: float = Field(60.0, ge=0, le=90)
    hours: int = Field(24, ge=1, le=168)


class OverpassRequest(BaseModel):
    satellite_id: str
    constellation_id: str | None = None
    ground_station_id: str
    min_elevation_deg: float = Field(5.0, ge=0, le=90)
    hours: int = Field(48, ge=1, le=168)


class OverpassWindowOut(BaseModel):
    aos: datetime
    los: datetime
    max_elevation: float
    duration_seconds: float


class ImagingWindowOut(BaseModel):
    aos: datetime
    los: datetime
    max_elevation_deg: float
    illumination_pct: float
    duration_seconds: float


@router.post(
    "/imaging-windows",
    response_model=list[ImagingWindowOut],
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def post_imaging_windows(
    body: ImagingWindowRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> list[ImagingWindowOut]:
    """Calculate imaging windows for a satellite over a target bounding box."""
    # Resolve satellite
    try:
        sat_uuid = uuid.UUID(body.satellite_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid satellite ID")

    constellation, _role, _deprecated = resolve_constellation(
        db, current_user, body.constellation_id
    )
    sat = (
        db.query(Satellite)
        .join(
            ConstellationSatellite,
            ConstellationSatellite.satellite_id == Satellite.id,
        )
        .filter(
            Satellite.id == sat_uuid,
            ConstellationSatellite.constellation_id == constellation.id,
            ConstellationSatellite.enabled.is_(True),
        )
        .first()
    )
    if not sat:
        raise AppError(
            "CONSTELLATION_FORBIDDEN",
            "Satellite is not accessible through this constellation.",
            status_code=403,
        )

    # Validate bbox
    bbox = body.bbox
    for key in ("sw_lat", "sw_lng", "ne_lat", "ne_lng"):
        if key not in bbox:
            raise HTTPException(
                status_code=400,
                detail=f"Missing bbox key: {key}",
            )

    now = datetime.now(timezone.utc)
    windows = calculate_imaging_windows(
        satellite={
            "id": str(sat.id),
            "tle_line1": sat.tle_line1,
            "tle_line2": sat.tle_line2,
        },
        bbox=bbox,
        start_time=now,
        end_time=now + timedelta(hours=body.hours),
        min_elevation_deg=body.min_elevation_deg,
        max_sun_angle_deg=body.max_sun_angle_deg,
    )

    return [
        ImagingWindowOut(
            aos=w["aos"],
            los=w["los"],
            max_elevation_deg=w["max_elevation_deg"],
            illumination_pct=w["illumination_pct"],
            duration_seconds=w["duration_seconds"],
        )
        for w in windows
    ]


@router.post(
    "/overpass",
    response_model=list[OverpassWindowOut],
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def post_overpass(
    body: OverpassRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> list[OverpassWindowOut]:
    """Calculate ground-station overpass windows for a satellite."""
    # Resolve satellite
    try:
        sat_uuid = uuid.UUID(body.satellite_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid satellite ID")

    constellation, _role, _deprecated = resolve_constellation(
        db, current_user, body.constellation_id
    )
    sat = (
        db.query(Satellite)
        .join(
            ConstellationSatellite,
            ConstellationSatellite.satellite_id == Satellite.id,
        )
        .filter(
            Satellite.id == sat_uuid,
            ConstellationSatellite.constellation_id == constellation.id,
            ConstellationSatellite.enabled.is_(True),
        )
        .first()
    )
    if not sat:
        raise AppError(
            "CONSTELLATION_FORBIDDEN",
            "Satellite is not accessible through this constellation.",
            status_code=403,
        )

    # Resolve ground station
    try:
        gs_uuid = uuid.UUID(body.ground_station_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ground station ID")

    gs = db.query(GroundStation).filter(GroundStation.id == gs_uuid).first()
    if not gs:
        raise HTTPException(status_code=404, detail="Ground station not found")

    now = datetime.now(timezone.utc)
    windows = calculate_overpass_windows(
        satellite={
            "id": str(sat.id),
            "tle_line1": sat.tle_line1,
            "tle_line2": sat.tle_line2,
        },
        ground_station={
            "id": str(gs.id),
            "latitude": gs.latitude,
            "longitude": gs.longitude,
            "altitude_m": gs.altitude_m,
        },
        start_time=now,
        end_time=now + timedelta(hours=body.hours),
        min_elevation_deg=max(sat.min_elevation_deg, body.min_elevation_deg),
    )

    return [
        OverpassWindowOut(
            aos=w.aos,
            los=w.los,
            max_elevation=w.max_elevation_deg,
            duration_seconds=w.duration_seconds,
        )
        for w in windows
    ]
