"""Enforce npm high/critical advisories with narrow, expiring exceptions."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALLOWLIST = ROOT / "security/npm-audit-allowlist.json"
ENFORCED_SEVERITIES = {"high", "critical"}


@dataclass(frozen=True)
class AuditException:
    advisory: str
    packages: frozenset[str]
    expires: date
    reason: str


def _advisory_id(url: str) -> str:
    return Path(urlparse(url).path).name


def load_exceptions(path: Path) -> list[AuditException]:
    """Load and validate the reviewable exception file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("npm audit allowlist schema_version must be 1")

    exceptions: list[AuditException] = []
    for raw in payload.get("exceptions", []):
        advisory = raw.get("advisory")
        packages = raw.get("packages")
        expires = raw.get("expires")
        reason = raw.get("reason")
        if (
            not isinstance(advisory, str)
            or not advisory.startswith("GHSA-")
            or not isinstance(packages, list)
            or not packages
            or not all(isinstance(package, str) and package for package in packages)
            or not isinstance(expires, str)
            or not isinstance(reason, str)
            or not reason.strip()
        ):
            raise ValueError("invalid npm audit exception")
        exceptions.append(
            AuditException(
                advisory=advisory,
                packages=frozenset(packages),
                expires=date.fromisoformat(expires),
                reason=reason.strip(),
            )
        )
    return exceptions


def _root_advisories(
    package: str,
    vulnerabilities: dict[str, Any],
    visiting: frozenset[str] = frozenset(),
) -> set[str]:
    """Resolve npm's string-based transitive `via` links to GHSA roots."""
    if package in visiting:
        raise ValueError(f"cyclic npm audit dependency chain at {package}")
    vulnerability = vulnerabilities.get(package)
    if not isinstance(vulnerability, dict):
        raise ValueError(f"missing npm audit dependency referenced by {package}")

    roots: set[str] = set()
    for via in vulnerability.get("via", []):
        if isinstance(via, str):
            roots.update(
                _root_advisories(via, vulnerabilities, visiting | {package})
            )
        elif isinstance(via, dict):
            url = via.get("url")
            if isinstance(url, str):
                advisory = _advisory_id(url)
                if advisory.startswith("GHSA-"):
                    roots.add(advisory)
    return roots


def evaluate_audit(
    report: dict[str, Any],
    exceptions: list[AuditException],
    today: date,
) -> tuple[list[str], list[str]]:
    """Return accepted exception messages and policy failures."""
    if report.get("auditReportVersion") != 2:
        return [], ["npm did not return an auditReportVersion 2 report"]
    vulnerabilities = report.get("vulnerabilities")
    if not isinstance(vulnerabilities, dict):
        return [], ["npm audit report has no vulnerabilities object"]

    accepted: list[str] = []
    failures: list[str] = []
    for package, vulnerability in sorted(vulnerabilities.items()):
        if not isinstance(vulnerability, dict):
            failures.append(f"{package}: malformed vulnerability record")
            continue
        severity = vulnerability.get("severity")
        if severity not in ENFORCED_SEVERITIES:
            continue
        try:
            roots = _root_advisories(package, vulnerabilities)
        except ValueError as exc:
            failures.append(str(exc))
            continue
        if not roots:
            failures.append(f"{package}: {severity} advisory has no resolvable GHSA")
            continue

        package_exceptions: list[AuditException] = []
        for advisory in roots:
            matching = [
                exception
                for exception in exceptions
                if exception.advisory == advisory and package in exception.packages
            ]
            if not matching:
                failures.append(
                    f"{package}: {severity} {advisory} is not allowlisted"
                )
                continue
            exception = matching[0]
            if today > exception.expires:
                failures.append(
                    f"{package}: exception for {advisory} expired "
                    f"{exception.expires.isoformat()}"
                )
                continue
            package_exceptions.append(exception)

        if len(package_exceptions) == len(roots):
            advisories = ", ".join(sorted(roots))
            expiry = min(exception.expires for exception in package_exceptions)
            accepted.append(
                f"{package}: temporary exception for {advisories} "
                f"through {expiry.isoformat()}"
            )
    return accepted, failures


def run_npm_audit(project: Path) -> dict[str, Any]:
    """Run npm audit; a non-zero code is expected when advisories exist."""
    result = subprocess.run(
        ["npm", "audit", "--json"],
        cwd=project,
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise RuntimeError(f"npm audit did not return JSON: {detail}") from exc
    if "auditReportVersion" not in report:
        detail = report.get("message") or result.stderr.strip() or "unknown npm error"
        raise RuntimeError(f"npm audit failed: {detail}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=ROOT / "frontend")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST)
    args = parser.parse_args()

    try:
        report = (
            json.loads(args.input.read_text(encoding="utf-8"))
            if args.input
            else run_npm_audit(args.project)
        )
        exceptions = load_exceptions(args.allowlist)
        accepted, failures = evaluate_audit(
            report,
            exceptions,
            datetime.now(timezone.utc).date(),
        )
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"npm audit policy failure: {exc}")
        raise SystemExit(1) from exc

    for message in accepted:
        print(f"Accepted {message}")
    if failures:
        for failure in failures:
            print(f"npm audit policy failure: {failure}")
        raise SystemExit(1)
    print(
        "npm high/critical advisory policy passed"
        f" ({len(accepted)} package exception(s))."
    )


if __name__ == "__main__":
    main()
