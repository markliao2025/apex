"""Load, validate, hash, and replay the repository's synthetic event."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.core.errors import AppError
from app.schemas.demo import ConjunctionEvent

FIXTURE_ID = "apex-synthetic-001"
REPOSITORY_ROOT = Path(
    os.environ.get("APEX_REPO_ROOT", str(Path(__file__).resolve().parents[3]))
)
FIXTURE_ROOT = REPOSITORY_ROOT / "fixtures" / "demo" / "conjunction" / FIXTURE_ID


def canonical_json_sha256(value: Any) -> str:
    canonical = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def load_event() -> tuple[ConjunctionEvent, dict[str, Any], str]:
    try:
        raw = json.loads((FIXTURE_ROOT / "event.json").read_text(encoding="utf-8"))
        event = ConjunctionEvent.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise AppError(
            "DEMO_FIXTURE_INVALID",
            "The repository demo fixture is invalid.",
            status_code=500,
        ) from exc
    return event, raw, canonical_json_sha256(raw)


def build_replay() -> dict[str, Any]:
    event, _raw, fixture_hash = load_event()
    replay_id = str(
        uuid.uuid5(uuid.NAMESPACE_URL, f"apex:{event.event_id}:{fixture_hash}")
    )
    return {
        "schema_version": "apex.demo.replay.v1",
        "replay_id": replay_id,
        "fixture_id": FIXTURE_ID,
        "fixture_sha256": fixture_hash,
        "event_id": event.event_id,
        "created_at_utc": event.created_at_utc.isoformat().replace("+00:00", "Z"),
        "tca_utc": event.tca_utc.isoformat().replace("+00:00", "Z"),
        "objects": {
            "primary": event.primary.model_dump(),
            "secondary": event.secondary.model_dump(),
        },
        "relative_state": event.relative_state.model_dump(),
        "risk": {
            "collision_probability": event.risk.collision_probability,
            "source": event.risk.source,
            "method": event.risk.method,
        },
        "labels": {
            "pc_origin": "provided",
            "apex_computed_pc": False,
            "physics_verified": False,
        },
        "data_quality": {
            "grade": "degraded",
            "covariance_available": False,
            "pc_reproducible": False,
            "explanation": (
                "Covariance is unavailable; Apex cannot independently reproduce "
                "the provided collision probability."
            ),
        },
        "warnings": [
            (
                "Research and decision-support software. Not flight-certified. "
                "No maneuver is executed by Apex."
            ),
            "Synthetic event: do not use for operational decisions.",
            "Pc is provided by the fixture and is not computed by Apex.",
            "No maneuver trajectory is generated.",
        ],
        "limitations": event.limitations,
    }


def require_replay(replay_id: str) -> dict[str, Any]:
    replay = build_replay()
    if replay_id != replay["replay_id"]:
        raise AppError("REPLAY_NOT_FOUND", "Replay not found.", status_code=404)
    return replay
