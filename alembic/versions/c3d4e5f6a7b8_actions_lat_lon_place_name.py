"""add latitude, longitude to actions for map events

Revision ID: c3d4e5f6a7b8
Revises: e8f9a0b1c2d3
Create Date: 2026-02-11

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "e8f9a0b1c2d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "actions",
        sa.Column("latitude", sa.Float(), nullable=True),
    )
    op.add_column(
        "actions",
        sa.Column("longitude", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("actions", "longitude")
    op.drop_column("actions", "latitude")
