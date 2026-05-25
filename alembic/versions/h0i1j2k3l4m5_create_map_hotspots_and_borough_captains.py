"""create map_areas, area_captains, and map_hotspots tables

Revision ID: h0i1j2k3l4m5
Revises: g9h0i1j2k3l4
Create Date: 2026-05-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "h0i1j2k3l4m5"
down_revision: str | Sequence[str] | None = "g9h0i1j2k3l4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "map_areas",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("map_campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("area_type", sa.String(length=50), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=True),
        sa.Column("parent_area_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("bounds", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["map_campaign_id"], ["map_campaigns.id"]),
        sa.ForeignKeyConstraint(["parent_area_id"], ["map_areas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("map_campaign_id", "slug", name="uq_map_area_campaign_slug"),
    )

    op.create_table(
        "area_captains",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("map_area_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("captain_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["captain_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["map_area_id"], ["map_areas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("map_area_id", "captain_user_id", name="uq_area_captain_area_user"),
    )

    op.create_table(
        "map_hotspots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("map_campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("map_area_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["map_area_id"], ["map_areas.id"]),
        sa.ForeignKeyConstraint(["map_campaign_id"], ["map_campaigns.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("map_hotspots")
    op.drop_table("area_captains")
    op.drop_table("map_areas")
