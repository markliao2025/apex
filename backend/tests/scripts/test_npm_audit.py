"""Tests for the expiring npm advisory exception policy."""

from __future__ import annotations

from datetime import date
import importlib.util
from pathlib import Path
import sys


def _load_audit_module():
    script = Path(__file__).resolve().parents[3] / "scripts/check_npm_audit.py"
    spec = importlib.util.spec_from_file_location("check_npm_audit", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _report(advisory: str = "GHSA-qwww-vcr4-c8h2") -> dict:
    return {
        "auditReportVersion": 2,
        "vulnerabilities": {
            "react-router": {
                "severity": "high",
                "via": [{"url": f"https://github.com/advisories/{advisory}"}],
            },
            "react-router-dom": {
                "severity": "high",
                "via": ["react-router"],
            },
        },
    }


def _exception(audit, *, expires: date):
    return audit.AuditException(
        advisory="GHSA-qwww-vcr4-c8h2",
        packages=frozenset({"react-router", "react-router-dom"}),
        expires=expires,
        reason="Browser-only SPA; no RSC or server actions.",
    )


def test_allows_only_named_packages_and_advisory_before_expiry() -> None:
    audit = _load_audit_module()

    accepted, failures = audit.evaluate_audit(
        _report(),
        [_exception(audit, expires=date(2026, 8, 8))],
        date(2026, 7, 25),
    )

    assert len(accepted) == 2
    assert failures == []


def test_rejects_an_unexpected_high_advisory() -> None:
    audit = _load_audit_module()

    accepted, failures = audit.evaluate_audit(
        _report("GHSA-unexpected"),
        [_exception(audit, expires=date(2026, 8, 8))],
        date(2026, 7, 25),
    )

    assert accepted == []
    assert failures == [
        "react-router: high GHSA-unexpected is not allowlisted",
        "react-router-dom: high GHSA-unexpected is not allowlisted",
    ]


def test_rejects_an_expired_exception() -> None:
    audit = _load_audit_module()

    accepted, failures = audit.evaluate_audit(
        _report(),
        [_exception(audit, expires=date(2026, 7, 24))],
        date(2026, 7, 25),
    )

    assert accepted == []
    assert failures == [
        "react-router: exception for GHSA-qwww-vcr4-c8h2 expired 2026-07-24",
        "react-router-dom: exception for GHSA-qwww-vcr4-c8h2 expired 2026-07-24",
    ]
