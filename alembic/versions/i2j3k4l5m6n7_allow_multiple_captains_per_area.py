"""allow multiple captains per map area

Revision ID: i2j3k4l5m6n7
Revises: h0i1j2k3l4m5
Create Date: 2026-05-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "i2j3k4l5m6n7"
down_revision: str | Sequence[str] | None = "h0i1j2k3l4m5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _unique_constraint_names(table: str) -> set[str]:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return {c["name"] for c in insp.get_unique_constraints(table) if c.get("name")}


def _column_nullable(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    for col in insp.get_columns(table):
        if col["name"] == column:
            return bool(col.get("nullable", True))
    return True


def upgrade() -> None:
    """Migrate legacy single-captain schema; no-op if h0 already created multi-captain tables."""
    op.execute("DELETE FROM area_captains WHERE captain_user_id IS NULL")

    if "uq_area_captain_map_area" in _unique_constraint_names("area_captains"):
        op.drop_constraint("uq_area_captain_map_area", "area_captains", type_="unique")

    if _column_nullable("area_captains", "captain_user_id"):
        op.alter_column(
            "area_captains",
            "captain_user_id",
            existing_type=postgresql.UUID(as_uuid=True),
            nullable=False,
        )

    if "uq_area_captain_area_user" not in _unique_constraint_names("area_captains"):
        op.create_unique_constraint(
            "uq_area_captain_area_user",
            "area_captains",
            ["map_area_id", "captain_user_id"],
        )


def downgrade() -> None:
    if "uq_area_captain_area_user" in _unique_constraint_names("area_captains"):
        op.drop_constraint("uq_area_captain_area_user", "area_captains", type_="unique")

    if not _column_nullable("area_captains", "captain_user_id"):
        op.alter_column(
            "area_captains",
            "captain_user_id",
            existing_type=postgresql.UUID(as_uuid=True),
            nullable=True,
        )

    if "uq_area_captain_map_area" not in _unique_constraint_names("area_captains"):
        op.create_unique_constraint("uq_area_captain_map_area", "area_captains", ["map_area_id"])
