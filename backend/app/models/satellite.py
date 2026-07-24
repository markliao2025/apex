"""Satellite model — stores orbital parameters and TLE data."""

import uuid

from sqlalchemy import Column, String, Float, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Satellite(Base):
    __tablename__ = "satellites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    norad_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    tle_line1 = Column(String(70), nullable=False)
    tle_line2 = Column(String(70), nullable=False)
    tle_epoch = Column(DateTime(timezone=True), nullable=False)
    orbit_type = Column(String(10), nullable=False)
    altitude_km_min = Column(Float, nullable=False)
    altitude_km_max = Column(Float, nullable=False)
    inclination_deg = Column(Float, nullable=False)
    eccentricity = Column(Float, nullable=False)
    payload_type = Column(String(20), nullable=False)
    max_resolution_m = Column(Float, nullable=False)
    swath_width_km = Column(Float, nullable=False)
    max_storage_gb = Column(Float, nullable=False)
    max_power_w = Column(Float, nullable=False)
    min_elevation_deg = Column(Float, server_default="5.0")
    turn_rate_deg_s = Column(Float, server_default="2.0")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    planned_tasks = relationship("PlannedTask", back_populates="satellite")
    constellation_links = relationship(
        "ConstellationSatellite",
        back_populates="satellite",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Satellite(norad_id={self.norad_id}, name={self.name})>"
