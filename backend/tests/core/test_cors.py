"""Browser-origin contract for the local Phase 0 frontend."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_local_frontend_preflight_is_allowed() -> None:
    response = client.options(
        "/api/v1/demo/status",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


def test_unlisted_browser_origin_is_not_allowed() -> None:
    response = client.options(
        "/api/v1/demo/status",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers
