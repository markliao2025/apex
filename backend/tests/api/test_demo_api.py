"""End-to-end API contract for the zero-credential synthetic demo."""

from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.database import get_db
from app.main import app
from app.models import Base
from app.scripts.bootstrap_demo import bootstrap_demo

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Session = sessionmaker(bind=engine)


def override_db():
    with Session() as db:
        yield db


def test_demo_session_replay_impact_and_export() -> None:
    Base.metadata.create_all(engine)
    with Session() as db:
        bootstrap_demo(db)

    app.dependency_overrides[get_db] = override_db
    settings = get_settings()
    previous = (
        settings.APP_ENV,
        settings.DEMO_MODE,
        settings.CONJUNCTION_DEMO_ENABLED,
    )
    settings.APP_ENV = "demo"
    settings.DEMO_MODE = True
    settings.CONJUNCTION_DEMO_ENABLED = True
    try:
        client = TestClient(app)
        status = client.get("/api/v1/demo/status")
        assert status.status_code == 200
        assert status.json()["status"] == "ready"
        assert status.json()["satellite_count"] == 2

        session = client.post("/api/v1/demo/session")
        assert session.status_code == 200
        headers = {"Authorization": f"Bearer {session.json()['access_token']}"}
        replay = client.post(
            "/api/v1/demo/replays",
            headers=headers,
            json={"fixture_id": "apex-synthetic-001"},
        )
        assert replay.status_code == 200
        replay_data = replay.json()
        assert replay_data["labels"]["pc_origin"] == "provided"
        assert replay_data["labels"]["apex_computed_pc"] is False

        constellation_id = status.json()["demo_constellation_id"]
        links = client.get(
            f"/api/v1/constellations/{constellation_id}/satellites",
            headers=headers,
        )
        satellite_id = links.json()[0]["satellite"]["id"]
        impact = client.post(
            f"/api/v1/demo/replays/{replay_data['replay_id']}/planning-impact",
            headers=headers,
            json={
                "constellation_id": constellation_id,
                "satellite_id": satellite_id,
                "unavailable_from_utc": "2024-06-01T11:30:00Z",
                "unavailable_to_utc": "2024-06-01T12:30:00Z",
                "reason": "synthetic_conjunction_what_if",
            },
        )
        assert impact.status_code == 200, impact.text
        assert impact.json()["before"]["task_count"] == 1
        assert impact.json()["after"]["task_count"] == 0
        assert impact.json()["algorithm_version"] == "apex.planning-impact.v1"
        assert len(impact.json()["evidence_sha256"]) == 64
        assert impact.json()["physics_verified"] is False
        assert any(
            "Not flight-certified" in limitation
            for limitation in impact.json()["limitations"]
        )

        exported = client.get(
            f"/api/v1/demo/replays/{replay_data['replay_id']}/export",
            headers=headers,
            params={"format": "md"},
        )
        assert exported.status_code == 200
        assert "Apex did not compute it" in exported.text
        assert "Not flight-certified" in exported.text
        assert "No maneuver is executed by Apex" in exported.text
    finally:
        (
            settings.APP_ENV,
            settings.DEMO_MODE,
            settings.CONJUNCTION_DEMO_ENABLED,
        ) = previous
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
