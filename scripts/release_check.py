"""Fast, deterministic checks required before a Phase 0 tag."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "LICENSE",
    "NOTICE",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "GOVERNANCE.md",
    "CHANGELOG.md",
    "README.md",
    "ROADMAP.md",
    "PHASE0_AI_EXECUTION_PLAN.md",
    "docs/legal/THIRD_PARTY_ASSETS.md",
    "docs/development/phase0-log.md",
    "fixtures/demo/conjunction/apex-synthetic-001/LICENSE.md",
]

FORBIDDEN_PARTS = {
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "coverage",
    "dist",
    "htmlcov",
    "node_modules",
    "outputs",
}
FORBIDDEN_SUFFIXES = {
    ".coverage",
    ".env",
    ".log",
    ".pyc",
    ".tsbuildinfo",
}


def find_forbidden_paths(tracked: list[str]) -> list[str]:
    """Return tracked paths that may not be shipped in a source release."""
    return [
        path
        for path in tracked
        if any(part in FORBIDDEN_PARTS for part in Path(path).parts)
        or any(path.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES)
        or path == "backend/de421.bsp"
    ]


def main() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit("Missing release files: " + ", ".join(missing))

    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if not tracked:
        raise SystemExit("Release check requires an initialized, tracked source tree.")

    forbidden = find_forbidden_paths(tracked)
    if forbidden:
        raise SystemExit("Forbidden tracked release files: " + ", ".join(forbidden))

    untracked_required = [path for path in REQUIRED_FILES if path not in tracked]
    if untracked_required:
        raise SystemExit(
            "Required release files are not tracked: " + ", ".join(untracked_required)
        )

    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if dirty:
        raise SystemExit(
            "Release check requires a clean source tree; first change: " + dirty[0]
        )

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required_phrases = [
        "make demo",
        "provided",
        "not for operational",
        "Apache-2.0",
    ]
    missing_phrases = [phrase for phrase in required_phrases if phrase not in readme]
    if missing_phrases:
        raise SystemExit("README is missing: " + ", ".join(missing_phrases))
    print("Release metadata and source boundary verified.")


if __name__ == "__main__":
    main()
