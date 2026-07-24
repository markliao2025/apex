"""Tenant-scope resolution shared by APIs and the planner."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Constellation, OrganizationMembership, User

WRITE_ROLES = {"owner", "operator"}


def accessible_constellation_rows(
    db: Session, user: User, organization_id: uuid.UUID | None = None
) -> list[tuple[Constellation, str]]:
    query = (
        db.query(Constellation, OrganizationMembership.role)
        .join(
            OrganizationMembership,
            OrganizationMembership.organization_id == Constellation.organization_id,
        )
        .filter(OrganizationMembership.user_id == user.id)
    )
    if organization_id is not None:
        query = query.filter(Constellation.organization_id == organization_id)
    return query.order_by(Constellation.name).all()


def constellation_access(
    db: Session, user: User, constellation_id: str | uuid.UUID
) -> tuple[Constellation, str]:
    try:
        identifier = (
            constellation_id
            if isinstance(constellation_id, uuid.UUID)
            else uuid.UUID(constellation_id)
        )
    except (TypeError, ValueError) as exc:
        raise AppError(
            "CONSTELLATION_FORBIDDEN",
            "You do not have access to this constellation.",
            status_code=403,
        ) from exc

    row = (
        db.query(Constellation, OrganizationMembership.role)
        .join(
            OrganizationMembership,
            OrganizationMembership.organization_id == Constellation.organization_id,
        )
        .filter(
            Constellation.id == identifier,
            OrganizationMembership.user_id == user.id,
        )
        .first()
    )
    if row is None:
        raise AppError(
            "CONSTELLATION_FORBIDDEN",
            "You do not have access to this constellation.",
            status_code=403,
            details={"constellation_id": str(identifier)},
        )
    return row


def resolve_constellation(
    db: Session, user: User, constellation_id: str | None
) -> tuple[Constellation, str, bool]:
    """Resolve explicit scope or the sole accessible scope for compatibility."""
    if constellation_id:
        constellation, role = constellation_access(db, user, constellation_id)
        return constellation, role, False

    rows = accessible_constellation_rows(db, user)
    if len(rows) != 1:
        raise AppError(
            "CONSTELLATION_REQUIRED",
            "Select a constellation before continuing.",
            status_code=400,
            details={"accessible_constellation_count": len(rows)},
        )
    constellation, role = rows[0]
    return constellation, role, True


def require_write_role(role: str) -> None:
    if role not in WRITE_ROLES:
        raise AppError(
            "CONSTELLATION_FORBIDDEN",
            "Your role cannot modify this constellation.",
            status_code=403,
        )
