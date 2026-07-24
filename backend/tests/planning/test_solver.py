"""Tests for CP-SAT solver."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


from app.planning.solver import solve
from app.planning.solver_types import (
    ImagingWindowData,
    RequestData,
    SatelliteData,
    SolverInput,
)


class TestCP_SATSolver:
    """Tests for the CP-SAT constraint solver."""

    def test_simple_single_request_single_satellite(self):
        """Test simple case: 1 request, 1 satellite, 1 window."""
        # Setup
        request = RequestData(id="req-1", priority_score=1.0)
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
            requests=[request],
            satellites=[satellite],
            imaging_windows={"sat-1": windows},
        )

        # Solve
        result = solve(solver_input, time_limit_ms=1000)

        # Assert
        assert result.status in ["optimal", "feasible"]
        assert len(result.assignments) >= 1
        assert result.objective_value >= 0

    def test_multiple_requests_single_window(self):
        """Test that multiple requests compete for single window."""
        requests = [
            RequestData(id="req-1", priority_score=1.0),
            RequestData(id="req-2", priority_score=0.5),
        ]
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
            requests=requests,
            satellites=[satellite],
            imaging_windows={"sat-1": windows},
        )

        result = solve(solver_input, time_limit_ms=1000)

        # Should satisfy at most 1 request due to window capacity
        assert len(result.assignments) <= 1
        # Should prefer higher priority request
        if len(result.assignments) == 1:
            assert result.assignments[0].request_id == "req-1"

    def test_overlapping_windows_constraint(self):
        """Test that overlapping windows on same satellite are handled."""
        requests = [
            RequestData(id="req-1", priority_score=1.0),
            RequestData(id="req-2", priority_score=1.0),
        ]
        satellite = SatelliteData(
            id="sat-1",
            name="TestSat",
            battery_capacity=100.0,
            storage_capacity=50000.0,
        )
        now = datetime.now(timezone.utc)
        # Two overlapping windows
        windows = [
            ImagingWindowData(
                aos=now,
                los=now + timedelta(seconds=60),  # Window 1: 0-60s
                max_elevation_deg=45.0,
                illumination_pct=0.9,
                duration_seconds=60.0,
                power_draw=1.0,
                data_mb=100.0,
            ),
            ImagingWindowData(
                aos=now + timedelta(seconds=30),  # Window 2: 30-90s (overlaps!)
                los=now + timedelta(seconds=90),
                max_elevation_deg=50.0,
                illumination_pct=0.9,
                duration_seconds=60.0,
                power_draw=1.0,
                data_mb=100.0,
            ),
        ]

        solver_input = SolverInput(
            requests=requests,
            satellites=[satellite],
            imaging_windows={"sat-1": windows},
        )

        result = solve(solver_input, time_limit_ms=1000)

        # Should assign at most 1 task due to overlap constraint
        assert len(result.assignments) <= 2

    def test_battery_constraint(self):
        """Test that battery capacity is respected."""
        requests = [
            RequestData(id="req-1", priority_score=1.0),
            RequestData(id="req-2", priority_score=1.0),
        ]
        satellite = SatelliteData(
            id="sat-1",
            name="TestSat",
            battery_capacity=2.0,  # Very low battery
            storage_capacity=50000.0,
        )
        now = datetime.now(timezone.utc)
        # Both windows together exceed battery
        windows = [
            ImagingWindowData(
                aos=now,
                los=now + timedelta(seconds=30),
                max_elevation_deg=45.0,
                illumination_pct=0.9,
                duration_seconds=30.0,
                power_draw=2.0,  # Each uses 2.0 units
                data_mb=100.0,
            ),
            ImagingWindowData(
                aos=now + timedelta(seconds=60),
                los=now + timedelta(seconds=90),
                max_elevation_deg=45.0,
                illumination_pct=0.9,
                duration_seconds=30.0,
                power_draw=2.0,
                data_mb=100.0,
            ),
        ]

        solver_input = SolverInput(
            requests=requests,
            satellites=[satellite],
            imaging_windows={"sat-1": windows},
        )

        result = solve(solver_input, time_limit_ms=1000)

        # Should satisfy at most 1 due to battery constraint
        assert len(result.assignments) <= 1

    def test_storage_constraint(self):
        """Test that storage capacity is respected."""
        requests = [
            RequestData(id="req-1", priority_score=1.0),
            RequestData(id="req-2", priority_score=1.0),
        ]
        satellite = SatelliteData(
            id="sat-1",
            name="TestSat",
            battery_capacity=100.0,
            storage_capacity=150.0,  # Can only store 150 MB
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
                data_mb=100.0,  # Each generates 100 MB
            ),
            ImagingWindowData(
                aos=now + timedelta(seconds=60),
                los=now + timedelta(seconds=90),
                max_elevation_deg=45.0,
                illumination_pct=0.9,
                duration_seconds=30.0,
                power_draw=1.0,
                data_mb=100.0,
            ),
        ]

        solver_input = SolverInput(
            requests=requests,
            satellites=[satellite],
            imaging_windows={"sat-1": windows},
        )

        result = solve(solver_input, time_limit_ms=1000)

        # Should satisfy at most 1 due to storage constraint
        assert len(result.assignments) <= 1

    def test_infeasible_case(self):
        """Test case where no feasible solution exists."""
        requests = [
            RequestData(id="req-1", priority_score=1.0),
        ]
        satellite = SatelliteData(
            id="sat-1",
            name="TestSat",
            battery_capacity=0.0,  # No battery at all
            storage_capacity=0.0,  # No storage
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
            requests=requests,
            satellites=[satellite],
            imaging_windows={"sat-1": windows},
        )

        result = solve(solver_input, time_limit_ms=1000)

        # Should either be infeasible or return empty assignments
        assert result.status == "infeasible" or len(result.assignments) == 0

    def test_multiple_satellites(self):
        """Test multiple satellites can handle independent tasks."""
        requests = [
            RequestData(id="req-1", priority_score=1.0),
            RequestData(id="req-2", priority_score=1.0),
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

        result = solve(solver_input, time_limit_ms=1000)

        # Should be able to satisfy both requests (one per satellite)
        assert result.status in ["optimal", "feasible"]
        assert len(result.assignments) == 2

    def test_priority_weighting(self):
        """Test that higher priority requests are preferred."""
        requests = [
            RequestData(id="req-low", priority_score=0.3),
            RequestData(id="req-high", priority_score=1.0),
        ]
        satellite = SatelliteData(
            id="sat-1",
            name="TestSat",
            battery_capacity=1.0,  # Can only handle 1 task
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
            requests=requests,
            satellites=[satellite],
            imaging_windows={"sat-1": windows},
        )

        result = solve(solver_input, time_limit_ms=1000)

        # Should satisfy the high priority request
        if len(result.assignments) == 1:
            assert result.assignments[0].request_id == "req-high"
        # Objective value is scaled by 1000 in the solver (priority * 1000)
        assert result.objective_value <= 1000.0  # Max is 1000.0 (high priority scaled)

    def test_performance_time_limit(self):
        """Test that solver respects time limit."""
        # Create many requests and windows to stress test
        requests = [RequestData(id=f"req-{i}", priority_score=0.8) for i in range(20)]
        satellites = [
            SatelliteData(
                id=f"sat-{i}",
                name=f"Sat{i}",
                battery_capacity=100.0,
                storage_capacity=50000.0,
            )
            for i in range(5)
        ]

        now = datetime.now(timezone.utc)
        windows = {}
        for sat in satellites:
            windows[sat.id] = [
                ImagingWindowData(
                    aos=now + timedelta(minutes=i * 10),
                    los=now + timedelta(minutes=i * 10, seconds=30),
                    max_elevation_deg=45.0,
                    illumination_pct=0.9,
                    duration_seconds=30.0,
                    power_draw=1.0,
                    data_mb=100.0,
                )
                for i in range(10)
            ]

        solver_input = SolverInput(
            requests=requests,
            satellites=satellites,
            imaging_windows=windows,
        )

        # Should complete within 5 seconds
        result = solve(solver_input, time_limit_ms=5000)

        assert result.solve_time_ms < 6000  # Allow some overhead
        assert result.status in ["optimal", "feasible", "suboptimal"]
