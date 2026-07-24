"""Enumerations used across all models."""

from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from enum import Enum as PyEnum


# ── Plan types ───────────────────────────────────────────────────────────────


class PlanType(str, PyEnum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# ── Orbit types ──────────────────────────────────────────────────────────────


class OrbitType(str, PyEnum):
    LEO = "leo"
    MEO = "meo"
    GEO = "geo"
    SSO = "sso"


# ── Payload types ────────────────────────────────────────────────────────────


class PayloadType(str, PyEnum):
    EO_OPTICAL = "eo_optical"
    EO_MULTISPECTRAL = "eo_multispectral"
    SAR = "sar"
    COMMS = "comms"


# ── Request status ───────────────────────────────────────────────────────────


class RequestStatus(str, PyEnum):
    PENDING = "pending"
    PLANNING = "planning"
    PLANNING_ERROR = "planning_error"
    READY = "ready"
    DEPLOYED = "deployed"
    CANCELLED = "cancelled"


# ── Solver status ────────────────────────────────────────────────────────────


class SolverStatus(str, PyEnum):
    OPTIMAL = "optimal"
    SUBOPTIMAL = "suboptimal"
    INFEASIBLE = "infeasible"


# ── Validator status ─────────────────────────────────────────────────────────


class ValidatorStatus(str, PyEnum):
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"


# ── Degradation types ────────────────────────────────────────────────────────


class DegradationType(str, PyEnum):
    CLOUD = "cloud"
    ILLUMINATION = "illumination"
    NOISE = "noise"
    JITTER = "jitter"
    RADIATION = "radiation"


# ── Model types ──────────────────────────────────────────────────────────────


class ModelType(str, PyEnum):
    CLASSIFICATION = "classification"
    DETECTION = "detection"
    SEGMENTATION = "segmentation"


# ── Severity levels ──────────────────────────────────────────────────────────


class SeverityLevel(str, PyEnum):
    NONE = "none"
    LIGHT = "light"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


# ── Mission profiles ─────────────────────────────────────────────────────────


class MissionProfile(str, PyEnum):
    TROPICAL = "tropical"
    POLAR = "polar"
    URBAN = "urban"
    ARCTIC = "arctic"


def sa_enum(enum_cls):
    """Return a SQLAlchemy ``Enum`` construct for the given Python enum.

    Uses PostgreSQL ``ENUM`` type when the dialect is postgresql,
    otherwise falls back to ``VARCHAR``-backed ``Enum``.
    """
    return PG_ENUM(enum_cls, name=enum_cls.__name__)
