"""Alembic migration script — initial 7 tables.

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(128), nullable=False),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("plan", sa.String(20), server_default="free", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── satellites ─────────────────────────────────────────────────────────
    op.create_table(
        "satellites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "norad_id", sa.String(length=20), unique=True, nullable=False, index=True
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("tle_line1", sa.String(70), nullable=False),
        sa.Column("tle_line2", sa.String(70), nullable=False),
        sa.Column("tle_epoch", sa.DateTime(timezone=True), nullable=False),
        sa.Column("orbit_type", sa.String(10), nullable=False),
        sa.Column("altitude_km_min", sa.Float(), nullable=False),
        sa.Column("altitude_km_max", sa.Float(), nullable=False),
        sa.Column("inclination_deg", sa.Float(), nullable=False),
        sa.Column("eccentricity", sa.Float(), nullable=False),
        sa.Column("payload_type", sa.String(20), nullable=False),
        sa.Column("max_resolution_m", sa.Float(), nullable=False),
        sa.Column("swath_width_km", sa.Float(), nullable=False),
        sa.Column("max_storage_gb", sa.Float(), nullable=False),
        sa.Column("max_power_w", sa.Float(), nullable=False),
        sa.Column("min_elevation_deg", sa.Float(), server_default="5.0"),
        sa.Column("turn_rate_deg_s", sa.Float(), server_default="2.0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    # ── ground_stations ────────────────────────────────────────────────────
    op.create_table(
        "ground_stations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("altitude_m", sa.Float(), nullable=False),
        sa.Column("min_elevation_deg", sa.Float(), server_default="5.0"),
        sa.Column("band", sa.String(20), nullable=False),
        sa.Column("antenna_diameter_m", sa.Float(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    # ── planning_requests ──────────────────────────────────────────────────
    op.create_table(
        "planning_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("raw_input", sa.Text(), nullable=False),
        sa.Column("parsed_intent", postgresql.JSONB(), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            server_default="pending",
            nullable=False,
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── planned_tasks ──────────────────────────────────────────────────────
    op.create_table(
        "planned_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "planning_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("planning_requests.id"),
            nullable=False,
        ),
        sa.Column(
            "satellite_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("satellites.id"),
            nullable=False,
        ),
        sa.Column(
            "ground_station_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ground_stations.id"),
            nullable=True,
        ),
        sa.Column("target_area", postgresql.JSONB(), nullable=False),
        sa.Column("event_window", postgresql.JSONB(), nullable=False),
        sa.Column("resource_allocation", postgresql.JSONB(), nullable=False),
        sa.Column(
            "solver_status",
            sa.String(20),
            server_default="optimal",
            nullable=False,
        ),
        sa.Column(
            "validator_status",
            sa.String(20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("priority_score", sa.Float(), server_default="0.5"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── evaluation_jobs ────────────────────────────────────────────────────
    op.create_table(
        "evaluation_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("model_name", sa.String(200), nullable=False),
        sa.Column("model_type", sa.String(50), nullable=False),
        sa.Column("sensor_type", sa.String(50), nullable=False),
        sa.Column("model_artifact_path", sa.String(500), nullable=False),
        sa.Column("baseline_dataset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("num_baseline_images", sa.Integer(), server_default="0"),
        sa.Column("degradation_types_enabled", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("progress_percent", sa.Integer(), server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── evaluation_results ─────────────────────────────────────────────────
    op.create_table(
        "evaluation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "evaluation_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evaluation_jobs.id"),
            nullable=False,
        ),
        sa.Column("degradation_type", sa.String(20), nullable=False),
        sa.Column("severity_level", sa.String(20), nullable=False),
        sa.Column("metrics", postgresql.JSONB(), nullable=False),
        sa.Column("robustness_score", sa.Float(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("evaluation_results")
    op.drop_table("evaluation_jobs")
    op.drop_table("planned_tasks")
    op.drop_table("planning_requests")
    op.drop_table("ground_stations")
    op.drop_table("satellites")
    op.drop_table("users")
