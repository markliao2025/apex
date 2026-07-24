"""Pytest configuration and shared fixtures for Apex backend tests."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from typing import Generator

import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import Base
from app.models import GroundStation, Satellite, User
from app.models.enums import OrbitType, PayloadType, PlanType
from app.core.security import hash_password, create_access_token


# ── Test Database Setup ──────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine using SQLite in-memory."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Import all models to ensure they're registered with Base
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ── Authentication Fixtures ──────────────────────────────────────────────────


@pytest.fixture
def test_user(db_session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestPassword123!"),
        name="Test User",
        plan=PlanType.FREE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user) -> dict:
    """Create authorization headers for test user."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def demo_user(db_session) -> User:
    """Create a demo user."""
    user = User(
        email="demo@apex.space",
        password_hash=hash_password("Demo123!"),
        name="Demo User",
        plan=PlanType.STARTER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ── Satellite Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def sample_satellite(db_session) -> Satellite:
    """Create a sample satellite with TLE data."""
    satellite = Satellite(
        norad_id=25544,  # ISS
        name="International Space Station",
        tle_line1="1 25544U 98067A   24152.50000000  .00016717  00000-0  10270-3 0  9993",
        tle_line2="2 25544  51.6400 247.8232 0006703 286.2345 146.0818 15.50105854345678",
        tle_epoch=datetime.now(timezone.utc),
        orbit_type=OrbitType.LEO,
        altitude_km_min=400.0,
        altitude_km_max=420.0,
        inclination_deg=51.64,
        eccentricity=0.0006703,
        payload_type=PayloadType.EO_OPTICAL,
        max_resolution_m=0.5,
        swath_width_km=15.0,
        max_storage_gb=100.0,
        max_power_w=50.0,
        min_elevation_deg=5.0,
        turn_rate_deg_s=2.0,
    )
    db_session.add(satellite)
    db_session.commit()
    db_session.refresh(satellite)
    return satellite


@pytest.fixture
def worldview3_satellite(db_session) -> Satellite:
    """Create a WorldView-3 like satellite."""
    satellite = Satellite(
        norad_id=40682,
        name="WorldView-3",
        tle_line1="1 35946U 09055A   24152.50972233 -.00000124  00000-0 -10210-4 0  9993",
        tle_line2="2 35946  97.9960 192.4280 0003211  83.5872 276.5870 14.23607746864585",
        tle_epoch=datetime.now(timezone.utc),
        orbit_type=OrbitType.SUN_SYNC,
        altitude_km_min=600.0,
        altitude_km_max=620.0,
        inclination_deg=97.996,
        eccentricity=0.0003211,
        payload_type=PayloadType.EO_OPTICAL,
        max_resolution_m=0.31,
        swath_width_km=13.1,
        max_storage_gb=1000.0,
        max_power_w=500.0,
        min_elevation_deg=5.0,
        turn_rate_deg_s=3.0,
    )
    db_session.add(satellite)
    db_session.commit()
    db_session.refresh(satellite)
    return satellite


@pytest.fixture
def rapid_eye_satellite(db_session) -> Satellite:
    """Create a RapidEye-like satellite."""
    satellite = Satellite(
        norad_id=37840,
        name="RapidEye-1",
        tle_line1="1 33312U 08034E   24152.45027805  .00000104  00000-0  29182-4 0  9993",
        tle_line2="2 33312  97.5545  51.1238 0001396 101.2345 258.9234 14.95312356723456",
        tle_epoch=datetime.now(timezone.utc),
        orbit_type=OrbitType.SUN_SYNC,
        altitude_km_min=600.0,
        altitude_km_max=620.0,
        inclination_deg=97.5545,
        eccentricity=0.0001396,
        payload_type=PayloadType.EO_MULTISPECTRAL,
        max_resolution_m=6.5,
        swath_width_km=77.0,
        max_storage_gb=500.0,
        max_power_w=300.0,
        min_elevation_deg=5.0,
        turn_rate_deg_s=2.0,
    )
    db_session.add(satellite)
    db_session.commit()
    db_session.refresh(satellite)
    return satellite


@pytest.fixture
def sentinel2_satellite(db_session) -> Satellite:
    """Create a Sentinel-2 like satellite."""
    satellite = Satellite(
        norad_id=40697,
        name="Sentinel-2A",
        tle_line1="1 40697U 15021A   24152.49861111  .00000324  00000-0  43145-4 0  9993",
        tle_line2="2 40697  98.5655 185.9673 0001234  67.8912 292.2567 14.30876521123456",
        tle_epoch=datetime.now(timezone.utc),
        orbit_type=OrbitType.SUN_SYNC,
        altitude_km_min=750.0,
        altitude_km_max=780.0,
        inclination_deg=98.5655,
        eccentricity=0.0001234,
        payload_type=PayloadType.EO_MULTISPECTRAL,
        max_resolution_m=10.0,
        swath_width_km=290.0,
        max_storage_gb=2000.0,
        max_power_w=600.0,
        min_elevation_deg=5.0,
        turn_rate_deg_s=1.5,
    )
    db_session.add(satellite)
    db_session.commit()
    db_session.refresh(satellite)
    return satellite


@pytest.fixture
def multiple_satellites(
    db_session,
    sample_satellite,
    worldview3_satellite,
    rapid_eye_satellite,
    sentinel2_satellite,
) -> list[Satellite]:
    """Create multiple satellites for testing."""
    return [
        sample_satellite,
        worldview3_satellite,
        rapid_eye_satellite,
        sentinel2_satellite,
    ]


# ── Ground Station Fixtures ───────────────────────────────────────────────────


@pytest.fixture
def tokyo_station(db_session) -> GroundStation:
    """Create Tokyo ground station."""
    station = GroundStation(
        name="Tokyo",
        latitude=35.6762,
        longitude=139.6503,
        altitude_m=40.0,
        min_elevation_deg=5.0,
        band="x_band",
        antenna_diameter_m=3.0,
    )
    db_session.add(station)
    db_session.commit()
    db_session.refresh(station)
    return station


@pytest.fixture
def nairobi_station(db_session) -> GroundStation:
    """Create Nairobi ground station."""
    station = GroundStation(
        name="Nairobi",
        latitude=-1.2921,
        longitude=36.8219,
        altitude_m=1700.0,
        min_elevation_deg=5.0,
        band="x_band",
        antenna_diameter_m=3.0,
    )
    db_session.add(station)
    db_session.commit()
    db_session.refresh(station)
    return station


# ── Fixture for satellite count verification ──────────────────────────────────


@pytest.fixture
def all_seed_satellites(
    db_session,
    sample_satellite,
    worldview3_satellite,
    rapid_eye_satellite,
    sentinel2_satellite,
) -> dict:
    """Return dict with count and list of all seed satellites."""
    satellites = db_session.query(Satellite).all()
    return {
        "count": len(satellites),
        "satellites": satellites,
        "names": [s.name for s in satellites],
        "norad_ids": [s.norad_id for s in satellites],
    }
