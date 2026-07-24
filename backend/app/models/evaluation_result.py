"""Evaluation result model — per-degradation-type output."""

import uuid

from sqlalchemy import Column, String, Float, Text, JSON, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_job_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("evaluation_jobs.id"), nullable=False
    )
    degradation_type = Column(String(20), nullable=False)
    severity_level = Column(String(20), nullable=False)
    metrics = Column(JSON, nullable=False)
    robustness_score = Column(Float, nullable=False)
    recommendation = Column(Text, nullable=False)
    generated_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    job = relationship("EvaluationJob", back_populates="results")

    def __repr__(self) -> str:
        return f"<EvaluationResult(degradation={self.degradation_type}, score={self.robustness_score})>"
