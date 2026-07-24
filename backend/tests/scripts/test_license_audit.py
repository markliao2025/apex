"""Tests for the release license policy."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_audit_module():
    script = Path(__file__).resolve().parents[3] / "scripts/audit_licenses.py"
    spec = importlib.util.spec_from_file_location("audit_licenses", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_license_policy_blocks_non_osi_restrictions() -> None:
    audit = _load_audit_module()

    assert audit.has_forbidden_license("Hippocratic-2.1")
    assert audit.has_forbidden_license("AGPL-3.0-only")
    assert audit.has_forbidden_license("BUSL-1.1")
    assert not audit.has_forbidden_license("Apache-2.0")
    assert not audit.has_forbidden_license("MIT OR BSD-3-Clause")
