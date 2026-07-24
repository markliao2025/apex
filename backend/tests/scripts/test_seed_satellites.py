"""Determinism and offline behavior for the Phase 0 demo bootstrap."""

from __future__ import annotations

import copy

import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.models import (
    Base,
    Constellation,
    ConstellationSatellite,
    GroundStation,
    Organization,
    OrganizationMembership,
    Satellite,
    User,
)
from app.scripts.bootstrap_demo import (
    DEMO_CONSTELLATION_ID,
    DEMO_ORG_ID,
    DEMO_USER_ID,
    bootstrap_demo,
)
from app.scripts.seed_satellites import (
    SATELLITE_CONFIGS,
    main,
    seed_satellites,
)

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Session = sessionmaker(bind=engine)


def setup_function() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def test_offline_seed_is_idempotent_and_does_not_mutate_configuration(
    monkeypatch,
) -> None:
    original_config = copy.deepcopy(SATELLITE_CONFIGS)

    def network_must_not_run(*_args, **_kwargs):
        raise AssertionError("offline seed attempted network access")

    monkeypatch.setattr(
        "app.scripts.seed_satellites.httpx.Client",
        network_must_not_run,
    )
    with Session() as db:
        first_count = seed_satellites(db, allow_network=False)
        first_rows = [
            (sat.norad_id, sat.tle_line1, sat.tle_epoch)
            for sat in db.query(Satellite).order_by(Satellite.norad_id)
        ]
        second_count = seed_satellites(db, allow_network=False)
        second_rows = [
            (sat.norad_id, sat.tle_line1, sat.tle_epoch)
            for sat in db.query(Satellite).order_by(Satellite.norad_id)
        ]

        assert first_count == 2
        assert second_count == 0
        assert first_rows == second_rows
        assert all(isinstance(row[0], str) for row in second_rows)
        assert {row[2].date().isoformat() for row in second_rows} == {"2024-05-31"}
        assert db.query(GroundStation).count() == 4

    assert SATELLITE_CONFIGS == original_config


def test_demo_bootstrap_has_stable_ids_and_link_counts() -> None:
    with Session() as db:
        bootstrap_demo(db)
        first_counts = {
            "users": db.query(User).count(),
            "organizations": db.query(Organization).count(),
            "memberships": db.query(OrganizationMembership).count(),
            "constellations": db.query(Constellation).count(),
            "links": db.query(ConstellationSatellite).count(),
            "satellites": db.query(Satellite).count(),
        }
        bootstrap_demo(db)
        second_counts = {
            "users": db.query(User).count(),
            "organizations": db.query(Organization).count(),
            "memberships": db.query(OrganizationMembership).count(),
            "constellations": db.query(Constellation).count(),
            "links": db.query(ConstellationSatellite).count(),
            "satellites": db.query(Satellite).count(),
        }

        assert first_counts == second_counts
        assert first_counts == {
            "users": 1,
            "organizations": 1,
            "memberships": 1,
            "constellations": 1,
            "links": 2,
            "satellites": 2,
        }
        assert db.get(User, DEMO_USER_ID) is not None
        assert db.get(Organization, DEMO_ORG_ID) is not None
        assert db.get(Constellation, DEMO_CONSTELLATION_ID) is not None


def test_seed_cli_rolls_back_and_reports_failure_to_the_process(monkeypatch) -> None:
    class FailingSession:
        rolled_back = False
        closed = False

        def rollback(self) -> None:
            self.rolled_back = True

        def close(self) -> None:
            self.closed = True

    session = FailingSession()
    monkeypatch.setattr(
        "app.scripts.seed_satellites.SessionLocal",
        lambda: session,
    )
    monkeypatch.setattr(
        "app.scripts.seed_satellites.seed_satellites",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("seed failed")),
    )

    with pytest.raises(RuntimeError, match="seed failed"):
        main()

    assert session.rolled_back is True
    assert session.closed is True
