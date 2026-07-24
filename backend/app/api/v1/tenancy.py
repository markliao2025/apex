"""Organization and constellation management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser, DbSession
from app.core.errors import AppError
from app.models import (
    Constellation,
    ConstellationSatellite,
    Organization,
    OrganizationMembership,
    Satellite,
)
from app.schemas.satellite import SatelliteOut
from app.schemas.tenancy import (
    ConstellationCreate,
    ConstellationOut,
    ConstellationSatelliteCreate,
    ConstellationSatelliteOut,
    ConstellationUpdate,
    OrganizationOut,
)
from app.services.tenancy import (
    accessible_constellation_rows,
    constellation_access,
    require_write_role,
)

router = APIRouter(tags=["Constellations"])


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


def _constellation_out(
    constellation: Constellation, role: str, db: Session
) -> ConstellationOut:
    count = (
        db.query(ConstellationSatellite)
        .filter(
            ConstellationSatellite.constellation_id == constellation.id,
            ConstellationSatellite.enabled.is_(True),
        )
        .count()
    )
    return ConstellationOut(
        id=str(constellation.id),
        organization_id=str(constellation.organization_id),
        slug=constellation.slug,
        name=constellation.name,
        description=constellation.description,
        is_demo=constellation.is_demo,
        role=role,
        satellite_count=count,
        created_at=constellation.created_at,
        updated_at=constellation.updated_at,
    )


@router.get("/organizations", response_model=list[OrganizationOut])
async def list_organizations(
    current_user: CurrentUser, db: DbSession
) -> list[OrganizationOut]:
    rows = (
        db.query(Organization, OrganizationMembership.role)
        .join(
            OrganizationMembership,
            OrganizationMembership.organization_id == Organization.id,
        )
        .filter(OrganizationMembership.user_id == current_user.id)
        .order_by(Organization.name)
        .all()
    )
    return [
        OrganizationOut(id=str(org.id), slug=org.slug, name=org.name, role=role)
        for org, role in rows
    ]


@router.get("/constellations", response_model=list[ConstellationOut])
async def list_constellations(
    current_user: CurrentUser,
    db: DbSession,
    organization_id: str | None = Query(None),
) -> list[ConstellationOut]:
    parsed_org_id = None
    if organization_id:
        try:
            parsed_org_id = uuid.UUID(organization_id)
        except ValueError as exc:
            raise AppError(
                "ORGANIZATION_FORBIDDEN",
                "You do not have access to this organization.",
                status_code=403,
            ) from exc
    return [
        _constellation_out(constellation, role, db)
        for constellation, role in accessible_constellation_rows(
            db, current_user, parsed_org_id
        )
    ]


@router.post(
    "/constellations",
    response_model=ConstellationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_constellation(
    body: ConstellationCreate, current_user: CurrentUser, db: DbSession
) -> ConstellationOut:
    try:
        org_id = uuid.UUID(body.organization_id)
    except ValueError as exc:
        raise AppError(
            "ORGANIZATION_FORBIDDEN",
            "You do not have access to this organization.",
            status_code=403,
        ) from exc
    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == current_user.id,
        )
        .first()
    )
    if membership is None:
        raise AppError(
            "ORGANIZATION_FORBIDDEN",
            "You do not have access to this organization.",
            status_code=403,
        )
    require_write_role(membership.role)
    constellation = Constellation(
        organization_id=org_id,
        slug=body.slug,
        name=body.name,
        description=body.description,
    )
    db.add(constellation)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(
            "CONSTELLATION_SLUG_CONFLICT",
            "That constellation slug is already in use.",
            status_code=409,
        ) from exc
    db.refresh(constellation)
    return _constellation_out(constellation, membership.role, db)


@router.get("/constellations/{constellation_id}", response_model=ConstellationOut)
async def get_constellation(
    constellation_id: str, current_user: CurrentUser, db: DbSession
) -> ConstellationOut:
    constellation, role = constellation_access(db, current_user, constellation_id)
    return _constellation_out(constellation, role, db)


@router.patch("/constellations/{constellation_id}", response_model=ConstellationOut)
async def update_constellation(
    constellation_id: str,
    body: ConstellationUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ConstellationOut:
    constellation, role = constellation_access(db, current_user, constellation_id)
    require_write_role(role)
    if body.name is not None:
        constellation.name = body.name
    if "description" in body.model_fields_set:
        constellation.description = body.description
    db.commit()
    db.refresh(constellation)
    return _constellation_out(constellation, role, db)


@router.get(
    "/constellations/{constellation_id}/satellites",
    response_model=list[ConstellationSatelliteOut],
)
async def list_constellation_satellites(
    constellation_id: str, current_user: CurrentUser, db: DbSession
) -> list[ConstellationSatelliteOut]:
    constellation, _role = constellation_access(db, current_user, constellation_id)
    links = (
        db.query(ConstellationSatellite)
        .filter(ConstellationSatellite.constellation_id == constellation.id)
        .join(Satellite)
        .order_by(Satellite.name)
        .all()
    )
    return [
        ConstellationSatelliteOut(
            constellation_id=str(link.constellation_id),
            display_name=link.display_name,
            enabled=link.enabled,
            satellite=_satellite_out(link.satellite),
        )
        for link in links
    ]


@router.post(
    "/constellations/{constellation_id}/satellites",
    response_model=ConstellationSatelliteOut,
)
async def attach_satellite(
    constellation_id: str,
    body: ConstellationSatelliteCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> ConstellationSatelliteOut:
    constellation, role = constellation_access(db, current_user, constellation_id)
    require_write_role(role)
    try:
        satellite_id = uuid.UUID(body.satellite_id)
    except ValueError as exc:
        raise AppError(
            "SATELLITE_NOT_FOUND", "Satellite not found.", status_code=404
        ) from exc
    satellite = db.query(Satellite).filter(Satellite.id == satellite_id).first()
    if satellite is None:
        raise AppError("SATELLITE_NOT_FOUND", "Satellite not found.", status_code=404)
    link = (
        db.query(ConstellationSatellite)
        .filter(
            ConstellationSatellite.constellation_id == constellation.id,
            ConstellationSatellite.satellite_id == satellite.id,
        )
        .first()
    )
    if link is None:
        link = ConstellationSatellite(
            constellation_id=constellation.id,
            satellite_id=satellite.id,
            display_name=body.display_name,
        )
        db.add(link)
    else:
        link.display_name = body.display_name
        link.enabled = True
    db.commit()
    db.refresh(link)
    return ConstellationSatelliteOut(
        constellation_id=str(link.constellation_id),
        display_name=link.display_name,
        enabled=link.enabled,
        satellite=_satellite_out(satellite),
    )


@router.delete(
    "/constellations/{constellation_id}/satellites/{satellite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def detach_satellite(
    constellation_id: str,
    satellite_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    constellation, role = constellation_access(db, current_user, constellation_id)
    require_write_role(role)
    try:
        parsed_satellite_id = uuid.UUID(satellite_id)
    except ValueError as exc:
        raise AppError(
            "SATELLITE_NOT_FOUND", "Satellite not found.", status_code=404
        ) from exc
    link = (
        db.query(ConstellationSatellite)
        .filter(
            ConstellationSatellite.constellation_id == constellation.id,
            ConstellationSatellite.satellite_id == parsed_satellite_id,
        )
        .first()
    )
    if link is not None:
        db.delete(link)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
