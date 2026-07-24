"""Planning request model — captures natural language user requests."""

import uuid

from sqlalchemy import Column, String, Text, JSON, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class PlanningRequest(Base):
    __tablename__ = "planning_requests"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    constellation_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("constellations.id"),
        nullable=False,
        index=True,
    )
    raw_input = Column(Text, nullable=False)
    parsed_intent = Column(JSON, nullable=True)
    status = Column(String(20), server_default="pending", nullable=False)
    error_code = Column(String(80), nullable=True)
    error_message = Column(String(500), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="planning_requests")
    tasks = relationship("PlannedTask", back_populates="request")
    constellation = relationship("Constellation", back_populates="planning_requests")

    def __repr__(self) -> str:
        return f"<PlanningRequest(id={self.id}, status={self.status})>"
