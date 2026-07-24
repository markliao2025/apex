"""Tests for physics validator."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


from app.planning.solver_types import (
    Assignment,
    ImagingWindowData,
    RequestData,
    SatelliteData,
    SolverInput,
)
from app.planning.validator import validate_task, run_validator


class TestPhysicsValidator:
    """Tests for the physics validation module."""

    def test_valid_task_passes(self):
        """Test that a valid task passes validation."""
        assignment = Assignment(
            request_id="req-1",
            satellite_id="sat-1",
            window_idx=0,
        )

        satellite = SatelliteData(
            id="sat-1",
            name="TestSat",
            battery_capacity=100.0,
            storage_capacity=50000.0,
        )

        now = datetime.now(timezone.utc)
        windows = [
            ImagingWindowData(
                aos=now,
                los=now + timedelta(seconds=30),
                max_elevation_deg=45.0,
                illumination_pct=0.9,
                duration_seconds=30.0,
                power_draw=1.0,
                data_mb=100.0,
            )
        ]

        solver_input = SolverInput(
            requests=[RequestData(id="req-1", priority_score=1.0)],
            satellites=[satellite],
            imaging_windows={"sat-1": windows},
        )

        result = validate_task(assignment, solver_input)

        assert result.passed is True
        assert len(result.violations) == 0

    def test_low_elevation_fails(self):
        """Test that low elevation angle fails validation."""
        assignment = Assignment(
            request_id="req-1",
            satellite_id="sat-1",
            window_idx=0,
        )

        satellite = SatelliteData(
            id="sat-1",
            name="TestSat",
            battery_capacity=100.0,
            storage_capacity=50000.0,
        )

        now = datetime.now(timezone.utc)
        windows = [
            ImagingWindowData(
                aos=now,
                los=now + timedelta(seconds=30),
                max_elevation_deg=3.0,  # Below 5° minimum
                illumination_pct=0.9,
                duration_seconds=30.0,
                power_draw=1.0,
                data_mb=100.0,
            )
        ]

        solver_input = SolverInput(
            requests=[RequestData(id="req-1", priority_score=1.0)],
            satellites=[satellite],
            imaging_windows={"sat-1": windows},
        )

        result = validate_task(assignment, solver_input)

        assert result.passed is False
        assert any("elevation" in v.lower() for v in result.violations)

    def test_low_illumination_fails(self):
        """Test that low illumination fails validation."""
        assignment = Assignment(
            request_id="req-1",
            satellite_id="sat-1",
            window_idx=0,
        )

        satellite = SatelliteData(
            id="sat-1",
            name="TestSat",
            battery_capacity=100.0,
            storage_capacity=50000.0,
        )

        now = datetime.now(timezone.utc)
        windows = [
            ImagingWindowData(
                aos=now,
                los=now + timedelta(seconds=30),
                max_elevation_deg=45.0,
                illumination_pct=0.05,  # Below 10% threshold
                duration_seconds=30.0,
                power_draw=1.0,
                data_mb=100.0,
            )
        ]

        solver_input = SolverInput(
            requests=[RequestData(id="req-1", priority_score=1.0)],
            satellites=[satellite],
            imaging_windows={"sat-1": windows},
        )

        result = validate_task(assignment, solver_input)

        assert result.passed is False
        assert any("illumination" in v.lower() for v in result.violations)

    def test_battery_insufficient_fails(self):
        """Test that insufficient battery fails validation."""
        assignment = Assignment(
            request_id="req-1",
            satellite_id="sat-1",
            window_idx=0,
        )

        satellite = SatelliteData(
            id="sat-1",
            name="TestSat",
            battery_capacity=100.0,
            storage_capacity=50000.0,
        )

        now = datetime.now(timezone.utc)
        windows = [
            ImagingWindowData(
                aos=now,
                los=now + timedelta(seconds=30),
                max_elevation_deg=45.0,
                illumination_pct=0.9,
                duration_seconds=30.0,
                power_draw=1.0,  # Requires 1.0 units
                data_mb=100.0,
            )
        ]

        solver_input = SolverInput(
            requests=[RequestData(id="req-1", priority_score=1.0)],
            satellites=[satellite],
            imaging_windows={"sat-1": windows},
        )

        # Pass battery_remaining=0.5 to simulate low battery
        result = validate_task(assignment, solver_input, battery_remaining=0.5)

        assert result.passed is False
        assert any("battery" in v.lower() for v in result.violations)

    def test_storage_insufficient_fails(self):
        """Test that insufficient storage fails validation."""
        assignment = Assignment(
            request_id="req-1",
            satellite_id="sat-1",
            window_idx=0,
        )

        satellite = SatelliteData(
            id="sat-1",
            name="TestSat",
            battery_capacity=100.0,
            storage_capacity=50000.0,
        )

        now = datetime.now(timezone.utc)
        windows = [
            ImagingWindowData(
                aos=now,
                los=now + timedelta(seconds=30),
                max_elevation_deg=45.0,
                illumination_pct=0.9,
                duration_seconds=30.0,
                power_draw=1.0,
                data_mb=100.0,  # Generates 100 MB
            )
        ]

        solver_input = SolverInput(
            requests=[RequestData(id="req-1", priority_score=1.0)],
            satellites=[satellite],
            imaging_windows={"sat-1": windows},
        )

        # Pass storage_remaining_mb=50 to simulate low storage
        result = validate_task(assignment, solver_input, storage_remaining_mb=50.0)

        assert result.passed is False
        assert any("storage" in v.lower() for v in result.violations)

    def test_invalid_satellite_id(self):
        """Test that non-existent satellite fails."""
        assignment = Assignment(
            request_id="req-1",
            satellite_id="sat-nonexistent",
            window_idx=0,
        )

        satellite = SatelliteData(
            id="sat-1",
            name="TestSat",
            battery_capacity=100.0,
            storage_capacity=50000.0,
        )

        solver_input = SolverInput(
            requests=[RequestData(id="req-1", priority_score=1.0)],
            satellites=[satellite],
            imaging_windows={},
        )

        result = validate_task(assignment, solver_input)

        assert result.passed is False
        assert any("not_found" in v.lower() for v in result.violations)


class TestRunValidator:
    """Tests for the run_validator function."""

    def test_run_validator_multiple_assignments(self):
        """Test validation of multiple assignments."""
        from app.planning.solver import solve

        requests = [
            RequestData(id="req-1", priority_score=1.0),
            RequestData(id="req-2", priority_score=0.8),
        ]
        satellites = [
            SatelliteData(
                id="sat-1",
                name="Sat1",
                battery_capacity=100.0,
                storage_capacity=50000.0,
            ),
            SatelliteData(
                id="sat-2",
                name="Sat2",
                battery_capacity=100.0,
                storage_capacity=50000.0,
            ),
        ]

        now = datetime.now(timezone.utc)
        windows = {
            "sat-1": [
                ImagingWindowData(
                    aos=now,
                    los=now + timedelta(seconds=30),
                    max_elevation_deg=45.0,
                    illumination_pct=0.9,
                    duration_seconds=30.0,
                    power_draw=1.0,
                    data_mb=100.0,
                )
            ],
            "sat-2": [
                ImagingWindowData(
                    aos=now,
                    los=now + timedelta(seconds=30),
                    max_elevation_deg=45.0,
                    illumination_pct=0.9,
                    duration_seconds=30.0,
                    power_draw=1.0,
                    data_mb=100.0,
                )
            ],
        }

        solver_input = SolverInput(
            requests=requests,
            satellites=satellites,
            imaging_windows=windows,
        )

        # First solve
        solver_result = solve(solver_input)

        # Then validate
        validation_result = run_validator(solver_result, solver_input)

        assert "total" in validation_result
        assert "passed" in validation_result
        assert "failed" in validation_result
        assert validation_result["total"] >= 0
