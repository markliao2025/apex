"""Audit the licenses of Apex's direct Python and Node dependencies.

This is intentionally a direct-dependency release gate. The release SBOM and
GitHub dependency review cover the full resolved graph; this check ensures that
maintainers cannot add a direct dependency with a missing or explicitly
non-open-source license without a visible failure.
"""

from __future__ import annotations

import argparse
import json
import re
from importlib import metadata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_LICENSE_MARKERS = (
    "agpl",
    "business source license",
    "bsl-1.1",
    "busl",
    "commons clause",
    "elastic license",
    "hippocratic",
    "server side public license",
    "sspl",
)


def has_forbidden_license(value: str) -> bool:
    """Return whether a normalized license string violates the release policy."""
    lowered = value.casefold()
    return any(marker in lowered for marker in FORBIDDEN_LICENSE_MARKERS)


def _python_requirement_names(requirements_path: Path) -> list[str]:
    names: set[str] = set()
    for raw_line in requirements_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name = re.split(r"[<>=!~\[]", line, maxsplit=1)[0].strip()
        if name:
            names.add(name)
    return sorted(names, key=str.casefold)


def _python_license(package_name: str) -> tuple[str, str]:
    package_metadata = metadata.metadata(package_name)
    version = metadata.version(package_name)
    values: list[str] = []
    for field in ("License-Expression", "License"):
        value = package_metadata.get(field)
        if value:
            values.append(value.strip())
    for classifier in package_metadata.get_all("Classifier") or []:
        if classifier.startswith("License :: "):
            values.append(classifier.removeprefix("License :: ").strip())
    license_value = " | ".join(dict.fromkeys(value for value in values if value))
    return version, license_value


def _node_license(package_dir: Path) -> tuple[str, str]:
    package = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
    raw_license: Any = package.get("license") or package.get("licenses")
    if isinstance(raw_license, str):
        license_value = raw_license
    else:
        license_value = json.dumps(raw_license, sort_keys=True) if raw_license else ""
    return str(package.get("version", "")), license_value


def collect_direct_dependency_licenses() -> list[dict[str, str]]:
    """Collect deterministic license records from the installed dependencies."""
    records: list[dict[str, str]] = []
    for package_name in _python_requirement_names(ROOT / "backend/requirements.txt"):
        version, license_value = _python_license(package_name)
        records.append(
            {
                "ecosystem": "python",
                "name": package_name,
                "version": version,
                "license": license_value,
            }
        )

    frontend_package = json.loads(
        (ROOT / "frontend/package.json").read_text(encoding="utf-8")
    )
    node_names = set(frontend_package.get("dependencies", {}))
    node_names.update(frontend_package.get("devDependencies", {}))
    for package_name in sorted(node_names, key=str.casefold):
        version, license_value = _node_license(
            ROOT / "frontend/node_modules" / package_name
        )
        records.append(
            {
                "ecosystem": "node",
                "name": package_name,
                "version": version,
                "license": license_value,
            }
        )
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    records = collect_direct_dependency_licenses()
    failures = [
        record
        for record in records
        if not record["license"] or has_forbidden_license(record["license"])
    ]
    report = {
        "policy": "direct dependencies require declared licenses; AGPL/SSPL/"
        "BUSL/Commons-Clause/Elastic/Hippocratic licenses are blocked",
        "dependencies": records,
        "failures": failures,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.json_output:
        args.json_output.write_text(rendered + "\n", encoding="utf-8")

    if failures:
        for failure in failures:
            print(
                "License policy failure: "
                f"{failure['ecosystem']}:{failure['name']} "
                f"({failure['license'] or 'missing license'})"
            )
        raise SystemExit(1)
    print(f"Direct dependency licenses verified: {len(records)} packages.")


if __name__ == "__main__":
    main()
