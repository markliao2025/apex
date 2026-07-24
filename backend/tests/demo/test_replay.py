"""Golden tests for the synthetic conjunction replay."""

import json

import pytest
from pydantic import ValidationError

from app.schemas.demo import ConjunctionEvent
from app.services.demo_replay import FIXTURE_ROOT, build_replay, load_event


def test_replay_matches_committed_golden_file() -> None:
    expected = json.loads(
        (FIXTURE_ROOT / "expected-replay.json").read_text(encoding="utf-8")
    )
    assert build_replay() == expected


def test_fixture_preserves_six_digit_catalog_ids_and_provided_pc() -> None:
    event, _raw, fixture_hash = load_event()
    assert event.primary.catalog_id == "100001"
    assert event.secondary.catalog_id == "100002"
    assert event.risk.source == "provided"
    assert len(fixture_hash) == 64


def test_missing_covariance_degrades_quality_without_computing_pc() -> None:
    replay = build_replay()
    assert replay["data_quality"]["grade"] == "degraded"
    assert replay["labels"]["pc_origin"] == "provided"
    assert replay["labels"]["apex_computed_pc"] is False
    assert any("Not flight-certified" in warning for warning in replay["warnings"])
    assert any("No maneuver is executed" in warning for warning in replay["warnings"])


def test_fixture_schema_rejects_untracked_extension_fields() -> None:
    raw = json.loads((FIXTURE_ROOT / "event.json").read_text(encoding="utf-8"))
    raw["risk"]["collision_probability_percent"] = 0.012

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ConjunctionEvent.model_validate(raw)
