"""add event_data JSON to actions for type-specific payloads

Revision ID: e5f6a7b8c9d0
Revises: c3d4e5f6a7b8
Create Date: 2026-02-11

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: str | Sequence[str] | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema. Add event_data only if missing (idempotent)."""
    op.execute(
        """
        ALTER TABLE actions
        ADD COLUMN IF NOT EXISTS event_data JSON
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE actions DROP COLUMN IF EXISTS event_data")
