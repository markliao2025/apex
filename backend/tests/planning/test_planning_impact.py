"""Deterministic hypothetical unavailable-window impact."""

from app.planning.impact import evaluate_planning_impact
from app.schemas.demo import UnavailableWindowInput


def test_unavailable_window_removes_synthetic_opportunity() -> None:
    body = UnavailableWindowInput.model_validate(
        {
            "constellation_id": "a0000000-0000-4000-8000-000000000002",
            "satellite_id": "00000000-0000-4000-8000-000000000010",
            "unavailable_from_utc": "2024-06-01T11:30:00Z",
            "unavailable_to_utc": "2024-06-01T12:30:00Z",
            "reason": "synthetic_conjunction_what_if",
        }
    )
    result = evaluate_planning_impact(body)
    assert result["before"]["task_count"] == 1
    assert result["after"]["task_count"] == 0
    assert len(result["diff"]["removed_task_ids"]) == 1
    assert result["physics_verified"] is False
    assert result["algorithm_version"] == "apex.planning-impact.v1"
    assert len(result["evidence_sha256"]) == 64


def test_impact_repeats_semantically() -> None:
    body = UnavailableWindowInput.model_validate(
        {
            "constellation_id": "a0000000-0000-4000-8000-000000000002",
            "satellite_id": "00000000-0000-4000-8000-000000000010",
            "unavailable_from_utc": "2024-06-01T11:30:00Z",
            "unavailable_to_utc": "2024-06-01T12:30:00Z",
            "reason": "synthetic_conjunction_what_if",
        }
    )
    first = evaluate_planning_impact(body)
    second = evaluate_planning_impact(body)
    first["before"].pop("solve_time_ms")
    first["after"].pop("solve_time_ms")
    second["before"].pop("solve_time_ms")
    second["after"].pop("solve_time_ms")
    assert first == second
    assert first["evidence_sha256"] == second["evidence_sha256"]


def test_non_overlapping_window_preserves_synthetic_opportunity() -> None:
    body = UnavailableWindowInput.model_validate(
        {
            "constellation_id": "a0000000-0000-4000-8000-000000000002",
            "satellite_id": "00000000-0000-4000-8000-000000000010",
            "unavailable_from_utc": "2024-06-01T13:00:00Z",
            "unavailable_to_utc": "2024-06-01T14:00:00Z",
            "reason": "synthetic_conjunction_what_if",
        }
    )

    result = evaluate_planning_impact(body)

    assert result["before"]["task_ids"] == result["after"]["task_ids"]
    assert result["before"]["objective_value"] == result["after"]["objective_value"]
    assert result["diff"]["removed_task_ids"] == []
    assert result["hypothesis"]["overlaps_synthetic_opportunity"] is False
    assert result["hypothesis"]["filter_reason"] is None
