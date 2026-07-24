"""Authorization tests for organization, constellation, and planning scopes."""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import (
    Base,
    OrganizationMembership,
    PlanningRequest,
    Satellite,
    User,
)

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Session = sessionmaker(bind=engine)


def override_db():
    with Session() as db:
        yield db


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    app.dependency_overrides[get_db] = override_db
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def register_and_login(email: str) -> tuple[dict, dict[str, str]]:
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "longpassword123",
            "name": email.split("@")[0],
        },
    )
    assert registered.status_code == 201
    logged_in = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "longpassword123"},
    )
    assert logged_in.status_code == 200
    return registered.json(), {
        "Authorization": f"Bearer {logged_in.json()['access_token']}"
    }


def first_constellation(headers: dict[str, str]) -> dict:
    response = client.get("/api/v1/constellations", headers=headers)
    assert response.status_code == 200
    return response.json()[0]


def add_planning_request(
    user_id: str,
    constellation_id: str,
    *,
    status: str,
) -> str:
    request_id = uuid.uuid4()
    with Session() as db:
        db.add(
            PlanningRequest(
                id=request_id,
                user_id=uuid.UUID(user_id),
                constellation_id=uuid.UUID(constellation_id),
                raw_input="Image Tokyo Bay during the next two days",
                status=status,
            )
        )
        db.commit()
    return str(request_id)


def test_registration_creates_accessible_default_constellation() -> None:
    _user, headers = register_and_login("owner@example.com")
    organizations = client.get("/api/v1/organizations", headers=headers)
    constellations = client.get("/api/v1/constellations", headers=headers)
    assert organizations.status_code == 200
    assert organizations.json()[0]["role"] == "owner"
    assert constellations.status_code == 200
    assert constellations.json()[0]["slug"] == "default"


def test_cross_tenant_constellation_is_not_visible() -> None:
    _a, headers_a = register_and_login("a@example.com")
    _b, headers_b = register_and_login("b@example.com")
    constellation_b = first_constellation(headers_b)

    response = client.get(
        f"/api/v1/constellations/{constellation_b['id']}",
        headers=headers_a,
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CONSTELLATION_FORBIDDEN"
    assert response.json()["error"]["trace_id"]


def test_viewer_cannot_modify_constellation() -> None:
    _user_a, headers_a = register_and_login("a@example.com")
    user_b, headers_b = register_and_login("b@example.com")
    constellation_a = first_constellation(headers_a)
    organization_a = client.get("/api/v1/organizations", headers=headers_a).json()[0]
    with Session() as db:
        db.add(
            OrganizationMembership(
                organization_id=uuid.UUID(organization_a["id"]),
                user_id=uuid.UUID(user_b["id"]),
                role="viewer",
            )
        )
        db.commit()

    response = client.patch(
        f"/api/v1/constellations/{constellation_a['id']}",
        headers=headers_b,
        json={"name": "Forbidden rename"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CONSTELLATION_FORBIDDEN"


def test_attach_is_idempotent_and_detach_does_not_delete_catalog_record() -> None:
    _user, headers = register_and_login("owner@example.com")
    constellation = first_constellation(headers)
    with Session() as db:
        satellite = Satellite(
            id=uuid.uuid4(),
            norad_id="100001",
            name="Synthetic catalog satellite",
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
        db.add(satellite)
        db.commit()
        satellite_id = str(satellite.id)

    path = f"/api/v1/constellations/{constellation['id']}/satellites"
    assert (
        client.post(
            path, headers=headers, json={"satellite_id": satellite_id}
        ).status_code
        == 200
    )
    assert (
        client.post(
            path, headers=headers, json={"satellite_id": satellite_id}
        ).status_code
        == 200
    )
    assert len(client.get(path, headers=headers).json()) == 1

    detached = client.delete(f"{path}/{satellite_id}", headers=headers)
    assert detached.status_code == 204
    with Session() as db:
        assert (
            db.query(Satellite).filter(Satellite.id == uuid.UUID(satellite_id)).count()
            == 1
        )


def test_user_without_constellation_gets_typed_required_error() -> None:
    user_id = uuid.uuid4()
    with Session() as db:
        db.add(
            User(
                id=user_id,
                email="isolated@example.com",
                password_hash=hash_password("longpassword123"),
            )
        )
        db.commit()
    token = create_access_token({"sub": str(user_id)})
    response = client.post(
        "/api/v1/planning/parse",
        headers={"Authorization": f"Bearer {token}"},
        json={"raw_input": "Image Tokyo Bay during the next two days"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "CONSTELLATION_REQUIRED"


def test_cross_tenant_planning_scope_is_forbidden_before_work_starts() -> None:
    _a, headers_a = register_and_login("a@example.com")
    _b, headers_b = register_and_login("b@example.com")
    constellation_b = first_constellation(headers_b)
    response = client.post(
        "/api/v1/planning/requests",
        headers=headers_a,
        json={
            "raw_input": "Image Tokyo Bay during the next two days",
            "constellation_id": constellation_b["id"],
        },
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CONSTELLATION_FORBIDDEN"


def test_parse_is_stateless_and_uses_only_constellation_assets() -> None:
    _user, headers = register_and_login("parser@example.com")
    constellation = first_constellation(headers)
    with Session() as db:
        satellite = Satellite(
            id=uuid.uuid4(),
            norad_id="100002",
            name="Parser context satellite",
            tle_line1="1 10002U 00001A   24152.50000000",
            tle_line2="2 10002  98.0000  10.0000 0001000 0 0 14.00000000",
            tle_epoch=datetime(2024, 5, 31, 12, tzinfo=timezone.utc),
            orbit_type="sso",
            altitude_km_min=500,
            altitude_km_max=500,
            inclination_deg=98,
            eccentricity=0.0001,
            payload_type="eo_multispectral",
            max_resolution_m=10,
            swath_width_km=100,
            max_storage_gb=100,
            max_power_w=100,
        )
        db.add(satellite)
        db.commit()
        satellite_id = str(satellite.id)
    client.post(
        f"/api/v1/constellations/{constellation['id']}/satellites",
        headers=headers,
        json={"satellite_id": satellite_id},
    )
    response = client.post(
        "/api/v1/planning/parse",
        headers=headers,
        json={
            "raw_input": "Image Tokyo Bay during the next two days",
            "constellation_id": constellation["id"],
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "parsed"
    assert "request_id" not in response.json()
    with Session() as db:
        assert db.query(PlanningRequest).count() == 0


@pytest.mark.parametrize(
    ("status", "expected_code"),
    [
        ("planning", "PLANNING_ALREADY_RUNNING"),
        ("cancelled", "INVALID_STATE"),
    ],
)
def test_replan_rejects_non_runnable_states(
    status: str,
    expected_code: str,
) -> None:
    user, headers = register_and_login(f"{status}@example.com")
    constellation = first_constellation(headers)
    request_id = add_planning_request(
        user["id"],
        constellation["id"],
        status=status,
    )

    response = client.post(
        f"/api/v1/planning/requests/{request_id}/replan",
        headers=headers,
        json={"priority_override": "urgent"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == expected_code


def test_replan_does_not_disclose_another_users_request() -> None:
    user_a, _headers_a = register_and_login("replan-a@example.com")
    _user_b, headers_b = register_and_login("replan-b@example.com")
    constellation_a = first_constellation(_headers_a)
    request_id = add_planning_request(
        user_a["id"],
        constellation_a["id"],
        status="planning_error",
    )

    response = client.post(
        f"/api/v1/planning/requests/{request_id}/replan",
        headers=headers_b,
        json={},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
