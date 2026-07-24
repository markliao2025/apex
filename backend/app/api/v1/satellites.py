"""Satellite listing, detail, and orbit endpoints for Apex."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query, Response

from app.api.dependencies import CurrentUser, DbSession
from app.core.errors import AppError
from app.models import ConstellationSatellite, GroundStation, Satellite
from app.schemas.satellite import SatelliteOut, OverpassWindow, GroundTrackPoint
from app.orbit.propagation import calculate_overpass_windows, calculate_ground_track
from app.schemas.common import ErrorResponse
from app.services.tenancy import resolve_constellation

router = APIRouter(tags=["Satellites"])


def _satellite_out(satellite: Satellite) -> SatelliteOut:
    return SatelliteOut(
        id=str(satellite.id),
        norad_id=satellite.norad_id,
        name=satellite.name,
        tle_epoch=satellite.tle_epoch,
        orbit_type=satellite.orbit_type,
        payload_type=satellite.payload_type,
        max_resolution_m=satellite.max_resolution_m,
        swath_width_km=satellite.swath_width_km,
    )


def _scoped_satellite(
    db: DbSession,
    current_user: CurrentUser,
    satellite_id: str,
    constellation_id: str | None,
) -> tuple[Satellite, bool]:
    constellation, _role, deprecated_fallback = resolve_constellation(
        db, current_user, constellation_id
    )
    try:
        sat_uuid = uuid.UUID(satellite_id)
    except ValueError as exc:
        raise AppError(
            "SATELLITE_NOT_FOUND", "Satellite not found.", status_code=404
        ) from exc
    satellite = (
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
    if satellite is None:
        raise AppError(
            "CONSTELLATION_FORBIDDEN",
            "Satellite is not accessible through this constellation.",
            status_code=403,
        )
    return satellite, deprecated_fallback


@router.get("/catalog", response_model=list[SatelliteOut])
async def list_satellite_catalog(
    current_user: CurrentUser, db: DbSession
) -> list[SatelliteOut]:
    """List the built-in public demo catalog; these are not tenant memberships."""
    return [
        _satellite_out(s) for s in db.query(Satellite).order_by(Satellite.name).all()
    ]


@router.get("/ground-stations/list", response_model=list[dict])
async def list_ground_stations(
    current_user: CurrentUser,
    db: DbSession,
) -> list[dict]:
    """List shared ground-station reference data."""
    stations = db.query(GroundStation).order_by(GroundStation.name).all()
    return [
        {
            "id": str(gs.id),
            "name": gs.name,
            "latitude": gs.latitude,
            "longitude": gs.longitude,
            "altitude_m": gs.altitude_m,
            "band": gs.band,
            "antenna_diameter_m": gs.antenna_diameter_m,
        }
        for gs in stations
    ]


@router.get(
    "/",
    response_model=list[SatelliteOut],
    responses={401: {"model": ErrorResponse}},
)
async def list_satellites(
    current_user: CurrentUser,
    db: DbSession,
    response: Response,
    constellation_id: str | None = Query(None),
) -> list[SatelliteOut]:
    """List all satellites available to the current user."""
    constellation, _role, deprecated_fallback = resolve_constellation(
        db, current_user, constellation_id
    )
    if deprecated_fallback:
        response.headers["Deprecation"] = "true"
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
        .order_by(Satellite.name)
        .all()
    )
    return [_satellite_out(s) for s in satellites]


@router.get(
    "/{satellite_id}",
    response_model=SatelliteOut,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def get_satellite(
    satellite_id: str,
    current_user: CurrentUser,
    db: DbSession,
    constellation_id: str | None = Query(None),
) -> SatelliteOut:
    """Get a single satellite by UUID."""
    sat, _deprecated = _scoped_satellite(
        db, current_user, satellite_id, constellation_id
    )
    return _satellite_out(sat)


@router.get(
    "/{satellite_id}/overpass",
    response_model=list[OverpassWindow],
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def get_satellite_overpass(
    satellite_id: str,
    current_user: CurrentUser,
    db: DbSession,
    ground_station_id: str = Query(..., description="Ground station UUID"),
    hours: int = Query(48, ge=1, le=168, description="Hours ahead to search"),
    constellation_id: str | None = Query(None),
) -> list[OverpassWindow]:
    """Calculate overpass windows for a satellite relative to a ground station."""
    # Resolve satellite
    sat, _deprecated = _scoped_satellite(
        db, current_user, satellite_id, constellation_id
    )

    # Resolve ground station
    try:
        gs_uuid = uuid.UUID(ground_station_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ground station ID")

    gs = db.query(GroundStation).filter(GroundStation.id == gs_uuid).first()
    if not gs:
        raise HTTPException(status_code=404, detail="Ground station not found")

    # Compute windows
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
        end_time=now + timedelta(hours=hours),
        min_elevation_deg=max(sat.min_elevation_deg, gs.min_elevation_deg),
    )

    return [
        OverpassWindow(
            aos=w.aos,
            los=w.los,
            max_elevation=w.max_elevation_deg,
            duration_seconds=w.duration_seconds,
        )
        for w in windows
    ]


@router.get(
    "/{satellite_id}/ground-track",
    response_model=list[GroundTrackPoint],
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def get_ground_track(
    satellite_id: str,
    current_user: CurrentUser,
    db: DbSession,
    hours: int = Query(24, ge=1, le=168),
    constellation_id: str | None = Query(None),
) -> list[GroundTrackPoint]:
    """Get satellite ground track points for map visualization."""
    sat, _deprecated = _scoped_satellite(
        db, current_user, satellite_id, constellation_id
    )

    now = datetime.now(timezone.utc)
    points = calculate_ground_track(
        satellite={
            "tle_line1": sat.tle_line1,
            "tle_line2": sat.tle_line2,
        },
        start_time=now,
        end_time=now + timedelta(hours=hours),
    )

    return [
        GroundTrackPoint(
            timestamp=p.timestamp,
            latitude=p.latitude,
            longitude=p.longitude,
            altitude_km=p.altitude_km,
        )
        for p in points
    ]
