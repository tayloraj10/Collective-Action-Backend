"""links: all FKs ON DELETE RESTRICT (block delete if linked)

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-02-28

Change project_id, initiative_id, and map_campaign_id foreign keys from
ON DELETE CASCADE to ON DELETE RESTRICT so deleting a project, initiative,
or map campaign fails until links referencing them are updated or removed.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8c9d0e1f2a3"
down_revision: str | Sequence[str] | None = "a7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PROJECT_FK_NAME = "links_project_id_fkey"
INITIATIVE_FK_NAME = "links_initiative_id_fkey"
MAP_CAMPAIGN_FK_NAME = "fk_links_map_campaign_id"


def upgrade() -> None:
    op.drop_constraint(PROJECT_FK_NAME, "links", type_="foreignkey")
    op.create_foreign_key(
        PROJECT_FK_NAME,
        "links",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(INITIATIVE_FK_NAME, "links", type_="foreignkey")
    op.create_foreign_key(
        INITIATIVE_FK_NAME,
        "links",
        "initiatives",
        ["initiative_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(MAP_CAMPAIGN_FK_NAME, "links", type_="foreignkey")
    op.create_foreign_key(
        MAP_CAMPAIGN_FK_NAME,
        "links",
        "map_campaigns",
        ["map_campaign_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(PROJECT_FK_NAME, "links", type_="foreignkey")
    op.create_foreign_key(
        PROJECT_FK_NAME,
        "links",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(INITIATIVE_FK_NAME, "links", type_="foreignkey")
    op.create_foreign_key(
        INITIATIVE_FK_NAME,
        "links",
        "initiatives",
        ["initiative_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(MAP_CAMPAIGN_FK_NAME, "links", type_="foreignkey")
    op.create_foreign_key(
        MAP_CAMPAIGN_FK_NAME,
        "links",
        "map_campaigns",
        ["map_campaign_id"],
        ["id"],
        ondelete="CASCADE",
    )
