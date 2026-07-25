"""Add Phase 0 organization and constellation tenancy.

Revision ID: 0002_phase0_tenancy
Revises: 0001_initial
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_phase0_tenancy"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

DEMO_ORG_ID = "a0000000-0000-4000-8000-000000000001"
DEMO_CONSTELLATION_ID = "a0000000-0000-4000-8000-000000000002"


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False),
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
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    op.create_table(
        "organization_memberships",
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            primary_key=True,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('owner', 'operator', 'viewer')",
            name="ck_organization_membership_role",
        ),
    )

    op.create_table(
        "constellations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_demo", sa.Boolean(), server_default=sa.false(), nullable=False),
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
        sa.UniqueConstraint(
            "organization_id", "slug", name="uq_constellation_org_slug"
        ),
    )
    op.create_index(
        "ix_constellations_organization_id",
        "constellations",
        ["organization_id"],
    )

    op.create_table(
        "constellation_satellites",
        sa.Column(
            "constellation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("constellations.id"),
            primary_key=True,
        ),
        sa.Column(
            "satellite_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("satellites.id"),
            primary_key=True,
        ),
        sa.Column("display_name", sa.String(160), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.add_column(
        "planning_requests",
        sa.Column("constellation_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "planning_requests", sa.Column("error_code", sa.String(80), nullable=True)
    )
    op.add_column(
        "planning_requests", sa.Column("error_message", sa.String(500), nullable=True)
    )
    op.create_foreign_key(
        "fk_planning_requests_constellation",
        "planning_requests",
        "constellations",
        ["constellation_id"],
        ["id"],
    )
    op.create_index(
        "ix_planning_requests_constellation_id",
        "planning_requests",
        ["constellation_id"],
    )

    # Stable demo scope for historical rows and deterministic bootstrap.
    op.execute(
        sa.text(
            """
            INSERT INTO organizations (id, slug, name)
            VALUES (CAST(:org_id AS uuid), 'apex-demo', 'Apex Demo')
            """
        ).bindparams(org_id=DEMO_ORG_ID)
    )
    op.execute(
        sa.text(
            """
            INSERT INTO constellations
                (id, organization_id, slug, name, description, is_demo)
            VALUES
                (CAST(:constellation_id AS uuid), CAST(:org_id AS uuid),
                 'demo-constellation', 'Demo constellation',
                 'Deterministic synthetic demo assets.', true)
            """
        ).bindparams(
            constellation_id=DEMO_CONSTELLATION_ID,
            org_id=DEMO_ORG_ID,
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO constellation_satellites (constellation_id, satellite_id)
            SELECT CAST(:constellation_id AS uuid), id FROM satellites
            ON CONFLICT DO NOTHING
            """
        ).bindparams(constellation_id=DEMO_CONSTELLATION_ID)
    )

    # Every historical user receives an isolated personal organization.
    op.execute(
        """
        INSERT INTO organizations (id, slug, name)
        SELECT id, 'personal-' || left(replace(id::text, '-', ''), 20), email || ' workspace'
        FROM users
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO organization_memberships (organization_id, user_id, role)
        SELECT id, id, 'owner' FROM users
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        sa.text(
            """
            INSERT INTO constellations
                (id, organization_id, slug, name, description, is_demo)
            SELECT
                md5(id::text || :constellation_suffix)::uuid,
                id,
                'default',
                'Default constellation',
                'Created by the Phase 0 tenancy migration.',
                false
            FROM users
            ON CONFLICT DO NOTHING
            """
        ).bindparams(constellation_suffix=":default")
    )
    # Provenance of legacy requests is not provable, so keep them in the
    # explicitly synthetic/demo scope rather than claiming personal ownership.
    op.execute(
        sa.text(
            """
            UPDATE planning_requests
            SET constellation_id = CAST(:constellation_id AS uuid)
            WHERE constellation_id IS NULL
            """
        ).bindparams(constellation_id=DEMO_CONSTELLATION_ID)
    )
    op.alter_column("planning_requests", "constellation_id", nullable=False)


def downgrade() -> None:
    op.drop_index(
        "ix_planning_requests_constellation_id", table_name="planning_requests"
    )
    op.drop_constraint(
        "fk_planning_requests_constellation", "planning_requests", type_="foreignkey"
    )
    op.drop_column("planning_requests", "error_message")
    op.drop_column("planning_requests", "error_code")
    op.drop_column("planning_requests", "constellation_id")
    op.drop_table("constellation_satellites")
    op.drop_index("ix_constellations_organization_id", table_name="constellations")
    op.drop_table("constellations")
    op.drop_table("organization_memberships")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
