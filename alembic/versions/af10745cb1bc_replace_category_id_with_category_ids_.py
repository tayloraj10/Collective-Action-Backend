"""Replace category_id with category_ids JSON on directory_of_good

Revision ID: af10745cb1bc
Revises: d71cc8e63bba
Create Date: 2026-04-27 20:42:13.027035

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af10745cb1bc'
down_revision: Union[str, Sequence[str], None] = 'd71cc8e63bba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('directory_of_good', sa.Column(
        'category_ids', sa.JSON(), nullable=True))
    # Migrate existing single category_id → one-element JSON array.
    op.execute(
        """
        UPDATE directory_of_good
        SET category_ids = json_build_array(category_id::text)
        WHERE category_id IS NOT NULL
        """
    )
    op.drop_constraint(op.f('directory_of_good_category_id_fkey'),
                       'directory_of_good', type_='foreignkey')
    op.drop_column('directory_of_good', 'category_id')


def downgrade() -> None:
    op.add_column('directory_of_good', sa.Column(
        'category_id', sa.UUID(), autoincrement=False, nullable=True))
    op.create_foreign_key(op.f('directory_of_good_category_id_fkey'),
                          'directory_of_good', 'categories', ['category_id'], ['id'])
    op.drop_column('directory_of_good', 'category_ids')
