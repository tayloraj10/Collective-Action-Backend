"""add description to initiatives

Revision ID: g9h0i1j2k3l4
Revises: f8a9b0c1d2e3
Create Date: 2026-05-17

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "g9h0i1j2k3l4"
down_revision: str | Sequence[str] | None = "f8a9b0c1d2e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("initiatives", sa.Column("description", sa.String(length=2000), nullable=True))


def downgrade() -> None:
    op.drop_column("initiatives", "description")
