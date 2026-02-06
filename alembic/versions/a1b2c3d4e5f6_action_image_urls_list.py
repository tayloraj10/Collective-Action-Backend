"""action image_url -> image_urls (list)

Revision ID: a1b2c3d4e5f6
Revises: bc08cc853347
Create Date: 2026-01-31

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "bc08cc853347"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add new column (JSON array of strings)
    op.add_column(
        "actions",
        sa.Column("image_urls", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    # Backfill: copy image_url into image_urls as [url] or []
    op.execute(
        """
        UPDATE actions
        SET image_urls = CASE
            WHEN image_url IS NOT NULL AND image_url != '' THEN json_build_array(image_url)
            ELSE '[]'::json
        END
        """
    )
    op.drop_column("actions", "image_url")


def downgrade() -> None:
    op.add_column(
        "actions",
        sa.Column("image_url", sa.String(length=512), nullable=True),
    )
    # Take first URL from list if present
    op.execute(
        """
        UPDATE actions
        SET image_url = CASE
            WHEN image_urls IS NOT NULL AND json_array_length(image_urls) > 0
            THEN image_urls->>0
            ELSE NULL
        END
        """
    )
    op.drop_column("actions", "image_urls")
