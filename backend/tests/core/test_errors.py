"""Central error mapping never leaks exception details."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import AppError, install_error_handlers


def build_app() -> FastAPI:
    test_app = FastAPI()
    install_error_handlers(test_app)

    @test_app.get("/typed")
    async def typed():
        raise AppError(
            "PLANNING_TIMEOUT",
            "Planning exceeded its time limit.",
            status_code=503,
            retryable=True,
        )

    @test_app.get("/unknown")
    async def unknown():
        raise RuntimeError("database-url-with-secret")

    return test_app


def test_typed_error_has_stable_envelope_and_trace_id() -> None:
    response = TestClient(build_app()).get(
        "/typed", headers={"X-Trace-ID": "test-trace"}
    )
    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "PLANNING_TIMEOUT",
            "message": "Planning exceeded its time limit.",
            "details": None,
            "retryable": True,
            "trace_id": "test-trace",
        }
    }


def test_unknown_error_is_redacted() -> None:
    response = TestClient(build_app(), raise_server_exceptions=False).get("/unknown")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "database-url-with-secret" not in response.text
