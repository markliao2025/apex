"""Evaluation job model — Rigor platform."""

import uuid

from sqlalchemy import Column, String, Integer, JSON, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class EvaluationJob(Base):
    __tablename__ = "evaluation_jobs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    model_name = Column(String(200), nullable=False)
    model_type = Column(String(50), nullable=False)
    sensor_type = Column(String(50), nullable=False)
    model_artifact_path = Column(String(500), nullable=False)
    baseline_dataset_id = Column(PG_UUID(as_uuid=True), nullable=True)
    num_baseline_images = Column(Integer, server_default="0")
    degradation_types_enabled = Column(JSON, nullable=False)
    status = Column(String(20), server_default="pending", nullable=False)
    progress_percent = Column(Integer, server_default="0")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="evaluation_jobs")
    results = relationship("EvaluationResult", back_populates="job")

    def __repr__(self) -> str:
        return f"<EvaluationJob(id={self.id}, status={self.status})>"
