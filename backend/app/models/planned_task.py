"""Planned task model — output of the CP-SAT solver + validator."""

import uuid

from sqlalchemy import Column, String, Float, Text, JSON, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class PlannedTask(Base):
    __tablename__ = "planned_tasks"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    planning_request_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("planning_requests.id"), nullable=False
    )
    satellite_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("satellites.id"), nullable=False
    )
    ground_station_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("ground_stations.id"), nullable=True
    )
    target_area = Column(JSON, nullable=False)
    event_window = Column(JSON, nullable=False)
    resource_allocation = Column(JSON, nullable=False)
    solver_status = Column(String(20), server_default="optimal", nullable=False)
    validator_status = Column(String(20), server_default="pending", nullable=False)
    failure_reason = Column(Text, nullable=True)
    priority_score = Column(Float, server_default="0.5")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    request = relationship("PlanningRequest", back_populates="tasks")
    satellite = relationship("Satellite", back_populates="planned_tasks")
    ground_station = relationship("GroundStation", back_populates="planned_tasks")

    def __repr__(self) -> str:
        return f"<PlannedTask(id={self.id}, solver={self.solver_status})>"
