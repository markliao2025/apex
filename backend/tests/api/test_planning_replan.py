"""Regression tests for background planning and replan state transitions."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.models import (
    Base,
    Constellation,
    ConstellationSatellite,
    Organization,
    OrganizationMembership,
    PlannedTask as PlannedTaskModel,
    PlanningRequest,
    Satellite,
    User,
)
from app.planning.intent import BoundingBox, ParsedIntent
from app.planning.planner import PlannedTask, PlanningResult
from app.services.planning_jobs import PUBLIC_FAILURE_MESSAGE, run_planning_job

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Session = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def reset_database() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def _seed_request(
    *, status: str = "planning"
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    user_id = uuid.uuid4()
    organization_id = uuid.uuid4()
    constellation_id = uuid.uuid4()
    satellite_id = uuid.uuid4()
    request_id = uuid.uuid4()
    with Session() as db:
        db.add(
            User(
                id=user_id,
                email=f"{user_id}@example.com",
                password_hash="not-used",
            )
        )
        db.add(
            Organization(
                id=organization_id,
                slug=f"org-{organization_id}",
                name="Test organization",
            )
        )
        db.add(
            OrganizationMembership(
                organization_id=organization_id,
                user_id=user_id,
                role="owner",
            )
        )
        db.add(
            Constellation(
                id=constellation_id,
                organization_id=organization_id,
                slug="test",
                name="Test constellation",
            )
        )
        db.add(
            Satellite(
                id=satellite_id,
                norad_id="100001",
                name="Synthetic satellite",
                tle_line1="1 10001U 00001A   24152.50000000",
                tle_line2="2 10001  98.0000  10.0000 0001000 0 0 14.00000000",
                tle_epoch=datetime(2024, 5, 31, 12, tzinfo=timezone.utc),
                orbit_type="sso",
                altitude_km_min=500,
                altitude_km_max=500,
                inclination_deg=98,
                eccentricity=0.0001,
                payload_type="eo_optical",
                max_resolution_m=10,
                swath_width_km=100,
                max_storage_gb=100,
                max_power_w=100,
            )
        )
        db.add(
            ConstellationSatellite(
                constellation_id=constellation_id,
                satellite_id=satellite_id,
                enabled=True,
            )
        )
        db.add(
            PlanningRequest(
                id=request_id,
                user_id=user_id,
                constellation_id=constellation_id,
                raw_input="Image Tokyo Bay during the next two days",
                status=status,
            )
        )
        db.add(
            PlannedTaskModel(
                id=uuid.uuid4(),
                planning_request_id=request_id,
                satellite_id=satellite_id,
                target_area={"kind": "old"},
                event_window={"kind": "old"},
                resource_allocation={"kind": "old"},
                validator_status="passed",
            )
        )
        db.commit()
    return request_id, constellation_id, satellite_id


def _result(request_id: uuid.UUID, satellite_id: uuid.UUID) -> PlanningResult:
    start = datetime(2024, 6, 1, 11, tzinfo=timezone.utc)
    intent = ParsedIntent(
        region_description="Tokyo Bay",
        bounding_box=BoundingBox(
            sw_lat=35.4,
            sw_lng=139.5,
            ne_lat=35.9,
            ne_lng=140.1,
        ),
        priority="urgent",
    )
    return PlanningResult(
        request_id=str(request_id),
        status="ready",
        parsed_intent=intent,
        tasks=[
            PlannedTask(
                id=str(
                    uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"apex-test:{request_id}:{satellite_id}",
                    )
                ),
                request_id=str(request_id),
                satellite_id=str(satellite_id),
                acquisition_start=start,
                acquisition_end=start + timedelta(minutes=5),
                max_elevation_deg=42,
                illumination_pct=0.8,
                duration_seconds=300,
                power_draw=20,
                data_mb=100,
                priority_score=4,
                validator_status="passed",
                validator_details={},
                violations=[],
                warnings=[],
            )
        ],
        validation_summary={"total": 1, "passed": 1, "failed": 0},
        explanation="Synthetic planning result",
        errors=[],
    )


def test_replan_replaces_tasks_and_rounds_horizon_up() -> None:
    request_id, constellation_id, satellite_id = _seed_request()
    observed: dict = {}

    def fake_planner(**kwargs):
        observed.update(kwargs)
        return _result(request_id, satellite_id)

    outcome = run_planning_job(
        session_factory=Session,
        request_id=request_id,
        raw_input="Image Tokyo Bay during the next two days",
        constellation_id=constellation_id,
        trace_id="trace-normal",
        replace_existing_tasks=True,
        preferred_satellite_id=str(satellite_id),
        priority_override="urgent",
        time_horizon_hours=25,
        planner=fake_planner,
    )

    assert outcome == "completed"
    assert observed["planning_horizon_days"] == 2
    assert observed["priority_override"] == "urgent"
    assert observed["request_id"] == str(request_id)
    with Session() as db:
        request = db.get(PlanningRequest, request_id)
        assert request is not None
        assert request.status == "ready"
        assert request.parsed_intent["priority"] == "urgent"
        assert len(request.tasks) == 1
        assert request.tasks[0].target_area["type"] == "Polygon"


def test_planner_error_is_redacted_and_traceable(
    caplog: pytest.LogCaptureFixture,
) -> None:
    request_id, constellation_id, _satellite_id = _seed_request()

    def failing_planner(**_kwargs):
        raise RuntimeError("postgresql://user:secret@example.invalid/apex")

    with caplog.at_level(logging.ERROR, logger="apex.planning"):
        outcome = run_planning_job(
            session_factory=Session,
            request_id=request_id,
            raw_input="Image Tokyo Bay during the next two days",
            constellation_id=constellation_id,
            trace_id="trace-redaction-test",
            replace_existing_tasks=True,
            planner=failing_planner,
        )

    assert outcome == "failed"
    assert "trace-redaction-test" in caplog.text
    with Session() as db:
        request = db.get(PlanningRequest, request_id)
        assert request is not None
        assert request.status == "planning_error"
        assert request.error_code == "PLANNING_REPLAN_ERROR"
        assert request.error_message == PUBLIC_FAILURE_MESSAGE
        assert "secret" not in request.error_message


def test_cancel_during_planner_execution_wins_the_race() -> None:
    request_id, constellation_id, satellite_id = _seed_request()

    def cancelling_planner(**kwargs):
        db = kwargs["db"]
        request = db.get(PlanningRequest, request_id)
        assert request is not None
        request.status = "cancelled"
        db.commit()
        return _result(request_id, satellite_id)

    outcome = run_planning_job(
        session_factory=Session,
        request_id=request_id,
        raw_input="Image Tokyo Bay during the next two days",
        constellation_id=constellation_id,
        trace_id="trace-cancel-race",
        replace_existing_tasks=True,
        planner=cancelling_planner,
    )

    assert outcome == "cancelled"
    with Session() as db:
        request = db.get(PlanningRequest, request_id)
        assert request is not None
        assert request.status == "cancelled"
        assert len(request.tasks) == 1
        assert request.tasks[0].target_area == {"kind": "old"}
