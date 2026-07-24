"""Fail when the committed synthetic replay differs from its golden output."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.demo_replay import FIXTURE_ROOT, build_replay  # noqa: E402


def main() -> None:
    expected = json.loads(
        (FIXTURE_ROOT / "expected-replay.json").read_text(encoding="utf-8")
    )
    actual = build_replay()
    if actual != expected:
        raise SystemExit(
            "Synthetic fixture replay differs from expected-replay.json. "
            "Review provenance and update the golden file deliberately."
        )
    print(f"Fixture verified: {actual['fixture_sha256']}")


if __name__ == "__main__":
    main()
