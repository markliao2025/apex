"""FastAPI application entry-point.

Registers routers, lifecycle events, and provides the ``/health`` endpoint.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1 import auth, demo, orbit, planning, satellites, tenancy
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.errors import install_error_handlers
from app.models import ConstellationSatellite, User
from app.scripts.bootstrap_demo import DEMO_CONSTELLATION_ID, DEMO_USER_ID

EXPECTED_DB_REVISION = "0002_phase0_tenancy"

settings = get_settings()

app = FastAPI(
    title="Apex",
    description=(
        "Satellite task planning AI Native agent (Apex) and orbital AI "
        "robustness evaluation platform (Rigor)."
    ),
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
)
install_error_handlers(app)


@app.get("/health/live", tags=["Operations"])
async def health_live():
    return {"status": "live", "version": app.version}


@app.get("/health/ready", tags=["Operations"])
async def health_ready():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            revision = db.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one_or_none()
            if revision != EXPECTED_DB_REVISION:
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "not_ready",
                        "checks": {
                            "database": "ok",
                            "migration": "not_at_head",
                        },
                    },
                )
            if settings.DEMO_MODE:
                demo_user_ready = (
                    db.query(User).filter(User.id == DEMO_USER_ID).first() is not None
                )
                demo_assets_ready = (
                    db.query(ConstellationSatellite)
                    .filter(
                        ConstellationSatellite.constellation_id == DEMO_CONSTELLATION_ID
                    )
                    .count()
                    > 0
                )
                if not (demo_user_ready and demo_assets_ready):
                    return JSONResponse(
                        status_code=503,
                        content={
                            "status": "not_ready",
                            "checks": {
                                "database": "ok",
                                "migration": "ok",
                                "demo_bootstrap": "failed",
                            },
                        },
                    )
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "checks": {"database": "failed"}},
        )
    return {
        "status": "ready",
        "checks": {
            "database": "ok",
            "migration": "ok",
            "demo_bootstrap": "ok" if settings.DEMO_MODE else "disabled",
        },
    }


@app.get("/health", tags=["Operations"], deprecated=True)
async def health_check():
    """Compatibility alias; new integrations should use /health/ready."""
    return await health_ready()


# ── Mount API routers ────────────────────────────────────────────────────────
# Each router is prefixed with /api/v1 to leave room for future versioning.

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(tenancy.router, prefix="/api/v1")
app.include_router(demo.router, prefix="/api/v1")
app.include_router(satellites.router, prefix="/api/v1/satellites", tags=["Satellites"])
app.include_router(orbit.router, prefix="/api/v1/orbit", tags=["Orbit Engine"])
app.include_router(planning.router, prefix="/api/v1/planning", tags=["Planning (Apex)"])
