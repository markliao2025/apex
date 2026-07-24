"""Ground station model."""

import uuid

from sqlalchemy import Column, String, Float, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class GroundStation(Base):
    __tablename__ = "ground_stations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude_m = Column(Float, nullable=False)
    min_elevation_deg = Column(Float, server_default="5.0")
    band = Column(String(20), nullable=False)
    antenna_diameter_m = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    planned_tasks = relationship("PlannedTask", back_populates="ground_station")

    def __repr__(self) -> str:
        return f"<GroundStation(name={self.name})>"
