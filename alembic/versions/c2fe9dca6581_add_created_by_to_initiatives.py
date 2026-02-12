"""add created_by to initiatives

Revision ID: c2fe9dca6581
Revises: f7a8b9c0d1e2
Create Date: 2026-02-10 02:39:00.205303

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c2fe9dca6581"
down_revision: str | Sequence[str] | None = "f7a8b9c0d1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "initiatives", sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        "fk_initiatives_created_by", "initiatives", "users", ["created_by"], ["id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_initiatives_created_by", "initiatives", type_="foreignkey")
    op.drop_column("initiatives", "created_by")
