"""Exercise the live synthetic demo API from session through planning impact."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

BASE_URL = os.environ.get("APEX_E2E_BASE_URL", "http://localhost:8000")


def request(path: str, *, method: str = "GET", token: str | None = None, body=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"Live demo is unavailable at {BASE_URL}. Run `make demo` first: {exc}"
        ) from exc


def main() -> None:
    status = request("/api/v1/demo/status")
    if status["status"] != "ready":
        raise SystemExit(f"Demo status is not ready: {status}")

    session = request("/api/v1/demo/session", method="POST")
    token = session["access_token"]
    replay = request(
        "/api/v1/demo/replays",
        method="POST",
        token=token,
        body={"fixture_id": "apex-synthetic-001"},
    )
    if replay["labels"] != {
        "pc_origin": "provided",
        "apex_computed_pc": False,
        "physics_verified": False,
    }:
        raise SystemExit(f"Unexpected replay labels: {replay['labels']}")

    constellation_id = status["demo_constellation_id"]
    links = request(
        f"/api/v1/constellations/{constellation_id}/satellites", token=token
    )
    impact = request(
        f"/api/v1/demo/replays/{replay['replay_id']}/planning-impact",
        method="POST",
        token=token,
        body={
            "constellation_id": constellation_id,
            "satellite_id": links[0]["satellite"]["id"],
            "unavailable_from_utc": "2024-06-01T11:30:00Z",
            "unavailable_to_utc": "2024-06-01T12:30:00Z",
            "reason": "synthetic_conjunction_what_if",
        },
    )
    if impact["before"]["task_count"] != 1 or impact["after"]["task_count"] != 0:
        raise SystemExit(f"Unexpected planning impact: {impact}")
    if impact["physics_verified"] is not False:
        raise SystemExit("Impact result must remain physics_verified=false")
    print("Live demo E2E passed: session -> replay -> constellation -> planning impact")
