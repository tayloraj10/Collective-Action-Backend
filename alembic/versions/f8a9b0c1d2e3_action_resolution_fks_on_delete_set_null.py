"""Set ON DELETE SET NULL on action resolution foreign keys.

Revision ID: f8a9b0c1d2e3
Revises: e4f5a6b7c8d9
Create Date: 2026-05-16

Allows deleting users or cleanup actions without FK violations; referencing
rows keep their resolution metadata except the cleared pointer column.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f8a9b0c1d2e3"
down_revision: str | Sequence[str] | None = "e4f5a6b7c8d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _drop_fk_if_exists(name: str) -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    fk_names = {fk["name"] for fk in insp.get_foreign_keys("actions")}
    if name in fk_names:
        op.drop_constraint(name, "actions", type_="foreignkey")


def upgrade() -> None:
    _drop_fk_if_exists("actions_resolved_by_user_id_fkey")
    _drop_fk_if_exists("actions_resolved_by_action_id_fkey")

    op.create_foreign_key(
        "actions_resolved_by_user_id_fkey",
        "actions",
        "users",
        ["resolved_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "actions_resolved_by_action_id_fkey",
        "actions",
        "actions",
        ["resolved_by_action_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    _drop_fk_if_exists("actions_resolved_by_user_id_fkey")
    _drop_fk_if_exists("actions_resolved_by_action_id_fkey")

    op.create_foreign_key(
        "actions_resolved_by_user_id_fkey",
        "actions",
        "users",
        ["resolved_by_user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "actions_resolved_by_action_id_fkey",
        "actions",
        "actions",
        ["resolved_by_action_id"],
        ["id"],
    )
