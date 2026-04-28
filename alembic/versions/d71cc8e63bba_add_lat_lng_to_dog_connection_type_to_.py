"""Add lat_lng to dog, connection_type to connections

Revision ID: d71cc8e63bba
Revises: 73137d40e351
Create Date: 2026-04-27 19:57:04.325144

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd71cc8e63bba'
down_revision: Union[str, Sequence[str], None] = '73137d40e351'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('connections', sa.Column('connection_type', sa.String(length=50), nullable=False, server_default='contribution'))
    op.add_column('directory_of_good', sa.Column('latitude', sa.Double(), nullable=True))
    op.add_column('directory_of_good', sa.Column('longitude', sa.Double(), nullable=True))


def downgrade() -> None:
    op.drop_column('directory_of_good', 'longitude')
    op.drop_column('directory_of_good', 'latitude')
    op.drop_column('connections', 'connection_type')
