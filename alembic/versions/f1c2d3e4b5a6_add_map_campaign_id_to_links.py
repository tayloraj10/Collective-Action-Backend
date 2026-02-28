"""add map_campaign_id to links (project links)

Revision ID: f1c2d3e4b5a6
Revises: b3c4d5e6f7a8
Create Date: 2026-02-28

Adds optional map_campaign_id to links and allows initiative_id to be nullable,
enforcing that exactly one target is set per link (initiative OR map campaign).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1c2d3e4b5a6"
down_revision: str | Sequence[str] | None = "b3c4d5e6f7a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "links",
        sa.Column("map_campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Allow map-campaign links where initiative_id is NULL
    op.alter_column(
        "links",
        "initiative_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )

    op.create_foreign_key(
        "fk_links_map_campaign_id",
        "links",
        "map_campaigns",
        ["map_campaign_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_unique_constraint(
        "uq_link_project_map_campaign",
        "links",
        ["project_id", "map_campaign_id"],
    )

    op.create_check_constraint(
        "ck_links_one_target",
        "links",
        "(initiative_id IS NOT NULL AND map_campaign_id IS NULL) OR "
        "(initiative_id IS NULL AND map_campaign_id IS NOT NULL)",
    )


def downgrade() -> None:
    # Downgrade safety: remove map-campaign links (they have initiative_id NULL)
    op.execute("DELETE FROM links WHERE initiative_id IS NULL")

    op.drop_constraint("ck_links_one_target", "links", type_="check")
    op.drop_constraint("uq_link_project_map_campaign", "links", type_="unique")
    op.drop_constraint("fk_links_map_campaign_id", "links", type_="foreignkey")

    op.drop_column("links", "map_campaign_id")

    op.alter_column(
        "links",
        "initiative_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

