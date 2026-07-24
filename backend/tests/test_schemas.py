"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.common import ErrorBody, ErrorResponse
from app.schemas.user import UserCreate
from app.schemas.planning import (
    ParsedIntent,
    ConfidenceScores,
    BoundingBox,
    ValidationResult,
)
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationReport,
    RobustnessScore,
)


class TestErrorResponse:
    def test_error_response_defaults(self):
        err = ErrorResponse(
            error=ErrorBody(code="TEST", message="test message", trace_id="trace")
        )
        assert err.error.code == "TEST"
        assert err.error.retryable is False

    def test_error_response_with_details(self):
        err = ErrorResponse(
            error=ErrorBody(
                code="FAIL",
                message="fail",
                details={"key": "val"},
                retryable=True,
                trace_id="trace",
            )
        )
        assert err.error.details == {"key": "val"}
        assert err.error.retryable is True


class TestUserCreate:
    def test_valid_user_create(self):
        user = UserCreate(email="a@b.com", password="longpassword")
        assert user.email == "a@b.com"

    def test_short_password_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(email="a@b.com", password="short")

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(email="not-an-email", password="longpassword")

    def test_name_max_length(self):
        user = UserCreate(email="a@b.com", password="longpassword", name="A" * 100)
        assert user.name == "A" * 100

    def test_name_too_long_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(email="a@b.com", password="longpassword", name="A" * 101)


class TestPlanningSchemas:
    def test_bbox_validation(self):
        bb = BoundingBox(sw_lat=35, sw_lng=139, ne_lat=36, ne_lng=140)
        assert bb.sw_lat == 35

    def test_parsed_intent_valid(self):
        intent = ParsedIntent(
            region_description="Tokyo Bay",
            bounding_box=BoundingBox(
                sw_lat=35.5, sw_lng=139.5, ne_lat=35.9, ne_lng=140.1
            ),
            resolution_requirement_m=3.0,
            time_window_days=2,
            priority="high",
            confidence=ConfidenceScores(
                region_description=0.95,
                resolution_requirement_m=0.9,
                time_window_days=0.95,
                priority=0.9,
            ),
        )
        assert intent.priority == "high"

    def test_priority_invalid_rejected(self):
        with pytest.raises(ValidationError):
            ParsedIntent(priority="invalid")


class TestEvaluationSchemas:
    def test_evaluation_create_valid(self):
        ev = EvaluationCreate(
            model_name="ShipDetector",
            model_type="detection",
            sensor_type="optical",
            degradation_types=["cloud", "illumination"],
        )
        assert ev.model_type == "detection"

    def test_evaluation_create_empty_degradation_rejected(self):
        with pytest.raises(ValidationError):
            EvaluationCreate(
                model_name="Test",
                model_type="classification",
                sensor_type="optical",
                degradation_types=[],
            )

    def test_robustness_score_range(self):
        score = RobustnessScore(overall=72.5, grade="B", per_degradation_type={})
        assert score.grade == "B"

    def test_recommendation_has_tag(self):
        report = EvaluationReport(
            summary="Model acceptable.",
            scores=RobustnessScore(overall=72.5, grade="B", per_degradation_type={}),
            metrics=[],
            recommendations=["Add cloud preprocessing."],
        )
        assert len(report.recommendations) == 1


class TestValidationResult:
    def test_passed_validation(self):
        vr = ValidationResult(passed=True, violations=[], warnings=[])
        assert vr.passed is True

    def test_failed_validation(self):
        vr = ValidationResult(
            passed=False,
            violations=["elevation_below_minimum"],
            warnings=["Battery margin tight"],
            details={"elevation_at_aos_deg": 2.5},
        )
        assert "elevation_below_minimum" in vr.violations
