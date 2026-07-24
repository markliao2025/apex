"""Tests for SQLAlchemy models — create instances and verify relationships."""

import uuid
import pytest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models import (
    User,
    Satellite,
    GroundStation,
    PlanningRequest,
    PlannedTask,
    EvaluationJob,
    EvaluationResult,
    Organization,
    OrganizationMembership,
    Constellation,
    ConstellationSatellite,
)


@pytest.fixture()
def engine():
    """In-memory SQLite engine for fast tests."""
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture()
def db_session(engine):
    """Fresh session per test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def create_personal_constellation(db_session, user: User) -> Constellation:
    organization = Organization(
        id=uuid.uuid4(),
        slug=f"org-{str(user.id)[:8]}",
        name="Test organization",
    )
    constellation = Constellation(
        id=uuid.uuid4(),
        organization=organization,
        slug="default",
        name="Default constellation",
    )
    db_session.add_all(
        [
            organization,
            OrganizationMembership(
                organization=organization,
                user=user,
                role="owner",
            ),
            constellation,
        ]
    )
    db_session.flush()
    return constellation


def test_user_create(db_session):
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="$2b$12$...",
        name="Test User",
        plan="free",
    )
    db_session.add(user)
    db_session.commit()
    fetched = db_session.query(User).filter_by(email="test@example.com").first()
    assert fetched is not None
    assert fetched.name == "Test User"
    assert fetched.plan == "free"


def test_satellite_create(db_session):
    sat = Satellite(
        id=uuid.uuid4(),
        norad_id="25544",
        name="ISS",
        tle_line1="1 25544U ...",
        tle_line2="2 25544U ...",
        tle_epoch=datetime.now(timezone.utc),
        orbit_type="leo",
        altitude_km_min=400.0,
        altitude_km_max=420.0,
        inclination_deg=51.6,
        eccentricity=0.0001,
        payload_type="eo_optical",
        max_resolution_m=0.5,
        swath_width_km=15.0,
        max_storage_gb=100.0,
        max_power_w=2000.0,
    )
    db_session.add(sat)
    db_session.commit()
    assert db_session.query(Satellite).count() == 1


def test_ground_station_create(db_session):
    gs = GroundStation(
        id=uuid.uuid4(),
        name="Tokyo",
        latitude=35.6762,
        longitude=139.6503,
        altitude_m=40.0,
        band="x_band",
        antenna_diameter_m=12.0,
    )
    db_session.add(gs)
    db_session.commit()
    assert db_session.query(GroundStation).count() == 1


def test_planning_request_create(db_session):
    user = User(
        id=uuid.uuid4(),
        email="pr@test.com",
        password_hash="hash",
    )
    db_session.add(user)
    db_session.flush()
    constellation = create_personal_constellation(db_session, user)

    pr = PlanningRequest(
        id=uuid.uuid4(),
        user_id=user.id,
        constellation_id=constellation.id,
        raw_input="Image Tokyo Bay next 48 hours",
        status="pending",
    )
    db_session.add(pr)
    db_session.commit()
    assert db_session.query(PlanningRequest).count() == 1


def test_planned_task_create(db_session):
    user = User(id=uuid.uuid4(), email="pt@test.com", password_hash="h")
    sat = Satellite(
        id=uuid.uuid4(),
        norad_id="25544",
        name="ISS",
        tle_line1="1 ...",
        tle_line2="2 ...",
        tle_epoch=datetime.now(timezone.utc),
        orbit_type="leo",
        altitude_km_min=400.0,
        altitude_km_max=420.0,
        inclination_deg=51.6,
        eccentricity=0.0001,
        payload_type="eo_optical",
        max_resolution_m=0.5,
        swath_width_km=15.0,
        max_storage_gb=100.0,
        max_power_w=2000.0,
    )
    db_session.add_all([user, sat])
    db_session.flush()
    constellation = create_personal_constellation(db_session, user)
    db_session.add(
        ConstellationSatellite(
            constellation_id=constellation.id,
            satellite_id=sat.id,
        )
    )

    pr = PlanningRequest(
        id=uuid.uuid4(),
        user_id=user.id,
        constellation_id=constellation.id,
        raw_input="test",
        status="pending",
    )
    db_session.add(pr)
    db_session.flush()

    task = PlannedTask(
        id=uuid.uuid4(),
        planning_request_id=pr.id,
        satellite_id=sat.id,
        target_area={"type": "Polygon", "coordinates": []},
        event_window={"aos": "2026-01-01T00:00:00Z", "los": "2026-01-01T00:01:00Z"},
        resource_allocation={"power_w": 100, "storage_mb": 50},
        solver_status="optimal",
        validator_status="passed",
    )
    db_session.add(task)
    db_session.commit()
    assert db_session.query(PlannedTask).count() == 1


def test_evaluation_flow(db_session):
    user = User(id=uuid.uuid4(), email="eval@test.com", password_hash="h")
    db_session.add(user)
    db_session.flush()

    job = EvaluationJob(
        id=uuid.uuid4(),
        user_id=user.id,
        model_name="TestNet",
        model_type="classification",
        sensor_type="optical",
        model_artifact_path="/tmp/model.onnx",
        degradation_types_enabled=["cloud", "illumination"],
        status="pending",
    )
    db_session.add(job)
    db_session.flush()

    result = EvaluationResult(
        id=uuid.uuid4(),
        evaluation_job_id=job.id,
        degradation_type="cloud",
        severity_level="moderate",
        metrics={"accuracy_clean": 0.9, "accuracy_degraded": 0.7},
        robustness_score=75.0,
        recommendation="Add cloud penetration preprocessing.",
    )
    db_session.add(result)
    db_session.commit()

    assert db_session.query(EvaluationJob).count() == 1
    assert db_session.query(EvaluationResult).count() == 1


def test_all_models_registered():
    """Verify all Phase 0 tables exist in Base.metadata."""
    expected = {
        "users",
        "satellites",
        "ground_stations",
        "planning_requests",
        "planned_tasks",
        "evaluation_jobs",
        "evaluation_results",
        "organizations",
        "organization_memberships",
        "constellations",
        "constellation_satellites",
    }
    actual = set(Base.metadata.tables.keys())
    assert actual == expected, (
        f"Missing: {expected - actual}; Extra: {actual - expected}"
    )


def test_all_datetime_columns_are_timezone_aware():
    datetime_columns = [
        column
        for table in Base.metadata.tables.values()
        for column in table.columns
        if hasattr(column.type, "timezone")
    ]

    assert datetime_columns
    assert all(column.type.timezone for column in datetime_columns)
