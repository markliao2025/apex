"""Tests for the Phase 0 source-release boundary."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_release_check_module():
    script = Path(__file__).resolve().parents[3] / "scripts/release_check.py"
    spec = importlib.util.spec_from_file_location("release_check", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_boundary_rejects_generated_and_sensitive_paths() -> None:
    release_check = _load_release_check_module()

    tracked = [
        "README.md",
        "backend/.env",
        "backend/.venv/bin/python",
        "frontend/node_modules/react/index.js",
        "frontend/dist/index.html",
        "backend/de421.bsp",
        "frontend/tsconfig.app.tsbuildinfo",
    ]

    assert release_check.find_forbidden_paths(tracked) == tracked[1:]


def test_release_boundary_allows_source_and_env_template() -> None:
    release_check = _load_release_check_module()

    assert (
        release_check.find_forbidden_paths(
            [
                "backend/.env.example",
                "frontend/src/main.tsx",
                "fixtures/demo/event.json",
            ]
        )
        == []
    )
