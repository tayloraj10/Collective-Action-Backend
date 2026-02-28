"""links: make project_id nullable, drop one-target check

Revision ID: a7b8c9d0e1f2
Revises: f1c2d3e4b5a6
Create Date: 2026-02-28

All three link IDs (project_id, initiative_id, map_campaign_id) are now nullable.
"""

from collections.abc import Sequence

from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: str | Sequence[str] | None = "f1c2d3e4b5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_links_one_target", "links", type_="check")
    op.alter_column(
        "links",
        "project_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    op.execute(
        "UPDATE links SET project_id = (SELECT id FROM projects LIMIT 1) WHERE project_id IS NULL"
    )
    op.alter_column(
        "links",
        "project_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.create_check_constraint(
        "ck_links_one_target",
        "links",
        "(initiative_id IS NOT NULL AND map_campaign_id IS NULL) OR "
        "(initiative_id IS NULL AND map_campaign_id IS NOT NULL)",
    )
