"""Idempotently create the stable local demo account and constellation."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import (
    Constellation,
    ConstellationSatellite,
    Organization,
    OrganizationMembership,
    Satellite,
    User,
)
from app.scripts.seed_satellites import seed_satellites

DEMO_ORG_ID = uuid.UUID("a0000000-0000-4000-8000-000000000001")
DEMO_CONSTELLATION_ID = uuid.UUID("a0000000-0000-4000-8000-000000000002")
DEMO_USER_ID = uuid.UUID("a0000000-0000-4000-8000-000000000003")
DEMO_EMAIL = "demo@apex.local"
DEMO_PASSWORD = "apex-demo-local-only"


def bootstrap_demo(db: Session) -> None:
    seed_satellites(db, allow_network=False)

    organization = db.query(Organization).filter(Organization.id == DEMO_ORG_ID).first()
    if organization is None:
        organization = Organization(id=DEMO_ORG_ID, slug="apex-demo", name="Apex Demo")
        db.add(organization)

    user = db.query(User).filter(User.id == DEMO_USER_ID).first()
    if user is None:
        user = User(
            id=DEMO_USER_ID,
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
            name="Demo Operator",
            plan="free",
        )
        db.add(user)
    db.flush()

    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.organization_id == DEMO_ORG_ID,
            OrganizationMembership.user_id == DEMO_USER_ID,
        )
        .first()
    )
    if membership is None:
        db.add(
            OrganizationMembership(
                organization_id=DEMO_ORG_ID,
                user_id=DEMO_USER_ID,
                role="owner",
            )
        )

    constellation = (
        db.query(Constellation)
        .filter(Constellation.id == DEMO_CONSTELLATION_ID)
        .first()
    )
    if constellation is None:
        constellation = Constellation(
            id=DEMO_CONSTELLATION_ID,
            organization_id=DEMO_ORG_ID,
            slug="demo-constellation",
            name="Demo constellation",
            description="Deterministic synthetic demo assets.",
            is_demo=True,
        )
        db.add(constellation)
    db.flush()

    for satellite in db.query(Satellite).all():
        link = (
            db.query(ConstellationSatellite)
            .filter(
                ConstellationSatellite.constellation_id == DEMO_CONSTELLATION_ID,
                ConstellationSatellite.satellite_id == satellite.id,
            )
            .first()
        )
        if link is None:
            db.add(
                ConstellationSatellite(
                    constellation_id=DEMO_CONSTELLATION_ID,
                    satellite_id=satellite.id,
                )
            )
    db.commit()


def main() -> None:
    with SessionLocal() as db:
        bootstrap_demo(db)
    print("Demo bootstrap complete.")


if __name__ == "__main__":
    main()
