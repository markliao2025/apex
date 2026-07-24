"""Evaluation-related Pydantic schemas for Rigor."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvaluationCreate(BaseModel):
    model_name: str = Field(..., min_length=1, max_length=200)
    model_type: str = Field(..., pattern="^(classification|detection|segmentation)$")
    sensor_type: str = Field(..., pattern="^(optical|multispectral|hyperspectral)$")
    degradation_types: List[str] = Field(
        ...,
        min_length=1,
        max_length=5,
    )
    mission_profile: Optional[str] = Field(
        None, pattern="^(tropical|polar|urban|arctic)$"
    )


class EvaluationJobOut(BaseModel):
    id: str
    model_name: str
    model_type: str
    sensor_type: str
    status: str
    progress_percent: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EvaluationResultOut(BaseModel):
    id: str
    degradation_type: str
    severity_level: str
    metrics: Dict[str, Any]
    robustness_score: float
    recommendation: str
    generated_at: datetime

    model_config = {"from_attributes": True}


class RobustnessScore(BaseModel):
    overall: float = Field(..., ge=0, le=100)
    grade: str = Field(..., pattern="^[A-F]$")
    per_degradation_type: Dict[str, Any] = Field(default_factory=dict)


class EvaluationReport(BaseModel):
    summary: str
    scores: RobustnessScore
    metrics: List[EvaluationResultOut]
    recommendations: List[str]
