"""make initiatives created_by NOT NULL (after backfill)

Revision ID: d3e4f5a6b7c8
Revises: c2fe9dca6581
Create Date: 2026-02-11

Backfills existing initiatives with NULL created_by using the first user id,
then alters the column to NOT NULL. Requires at least one user to exist.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3e4f5a6b7c8"
down_revision: str | Sequence[str] | None = "c2fe9dca6581"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Backfill NULL created_by then set column to NOT NULL."""
    # Backfill: set created_by to first user for any initiatives where it is NULL.
    # If there are no users, this leaves NULLs and the ALTER below will fail
    # with a clear constraint error (ensure at least one user exists before running).
    op.execute(
        sa.text("""
            UPDATE initiatives
            SET created_by = (SELECT id FROM users ORDER BY created_at ASC LIMIT 1)
            WHERE created_by IS NULL
        """)
    )

    # Now safe to make the column NOT NULL
    op.alter_column(
        "initiatives",
        "created_by",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )


def downgrade() -> None:
    """Revert created_by to nullable."""
    op.alter_column(
        "initiatives",
        "created_by",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
