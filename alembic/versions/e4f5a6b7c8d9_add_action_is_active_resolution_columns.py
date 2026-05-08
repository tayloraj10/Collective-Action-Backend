"""Add is_active and resolution columns to actions.

Revision ID: e4f5a6b7c8d9
Revises: af10745cb1bc
Create Date: 2026-05-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e4f5a6b7c8d9"
down_revision: str | Sequence[str] | None = "af10745cb1bc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("actions")}

    if "is_active" not in cols:
        op.add_column(
            "actions",
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
        )
    if "resolved_at" not in cols:
        op.add_column(
            "actions",
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "resolved_by_user_id" not in cols:
        op.add_column(
            "actions",
            sa.Column("resolved_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
    if "resolved_by_action_id" not in cols:
        op.add_column(
            "actions",
            sa.Column("resolved_by_action_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
    if "source_trash_report_id" not in cols:
        op.add_column(
            "actions",
            sa.Column("source_trash_report_id", postgresql.UUID(as_uuid=True), nullable=True),
        )

    insp = sa.inspect(bind)
    fk_names = {fk["name"] for fk in insp.get_foreign_keys("actions")}

    if "actions_resolved_by_user_id_fkey" not in fk_names:
        op.create_foreign_key(
            "actions_resolved_by_user_id_fkey",
            "actions",
            "users",
            ["resolved_by_user_id"],
            ["id"],
        )
    if "actions_resolved_by_action_id_fkey" not in fk_names:
        op.create_foreign_key(
            "actions_resolved_by_action_id_fkey",
            "actions",
            "actions",
            ["resolved_by_action_id"],
            ["id"],
        )
    if "actions_source_trash_report_id_fkey" not in fk_names:
        op.create_foreign_key(
            "actions_source_trash_report_id_fkey",
            "actions",
            "actions",
            ["source_trash_report_id"],
            ["id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    fk_names = {fk["name"] for fk in insp.get_foreign_keys("actions")}
    if "actions_source_trash_report_id_fkey" in fk_names:
        op.drop_constraint("actions_source_trash_report_id_fkey", "actions", type_="foreignkey")
    if "actions_resolved_by_action_id_fkey" in fk_names:
        op.drop_constraint("actions_resolved_by_action_id_fkey", "actions", type_="foreignkey")
    if "actions_resolved_by_user_id_fkey" in fk_names:
        op.drop_constraint("actions_resolved_by_user_id_fkey", "actions", type_="foreignkey")

    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("actions")}
    for name in (
        "source_trash_report_id",
        "resolved_by_action_id",
        "resolved_by_user_id",
        "resolved_at",
        "is_active",
    ):
        if name in cols:
            op.drop_column("actions", name)
