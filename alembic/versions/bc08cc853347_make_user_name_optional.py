"""initial schema

Revision ID: bc08cc853347
Revises: 
Create Date: 2026-01-23 08:30:22.295861

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bc08cc853347"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if tables exist before creating (for existing databases)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Create users table
    if 'users' not in existing_tables:
        op.create_table(
            'users',
            sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('firebase_user_id', sa.String(length=128), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('photo_url', sa.String(length=512), nullable=True),
            sa.Column('user_type', sa.String(length=50), nullable=False, server_default='person'),
            sa.Column('location', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column('social_links', postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('firebase_user_id'),
            sa.UniqueConstraint('email')
        )
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create categories table
    if 'categories' not in existing_tables:
        op.create_table(
            'categories',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
    
    # Create statuses table
    if 'statuses' not in existing_tables:
        op.create_table(
            'statuses',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('status_type', sa.String(length=100), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create action_types table
    if 'action_types' not in existing_tables:
        op.create_table(
            'action_types',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
    
    # Create quotes table
    if 'quotes' not in existing_tables:
        op.create_table(
            'quotes',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('text', sa.String(), nullable=False),
            sa.Column('translation', sa.String(), nullable=True),
            sa.Column('active', sa.Boolean(), nullable=True, server_default='true'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_quotes_id'), 'quotes', ['id'], unique=False)
    
    # Create actions table (depends on users)
    if 'actions' not in existing_tables:
        op.create_table(
            'actions',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('linked_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('action_type', sa.String(length=100), nullable=False),
            sa.Column('amount', sa.Float(), nullable=True),
            sa.Column('date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('image_url', sa.String(length=512), nullable=True),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create initiatives table (depends on categories and statuses)
    if 'initiatives' not in existing_tables:
        op.create_table(
            'initiatives',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('action', sa.String(length=100), nullable=False),
            sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('goal', sa.Integer(), nullable=True),
            sa.Column('complete', sa.Integer(), nullable=True),
            sa.Column('link', sa.String(length=512), nullable=True),
            sa.Column('priority', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('status_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
            sa.ForeignKeyConstraint(['status_id'], ['statuses.id']),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('initiatives')
    op.drop_table('actions')
    op.drop_index(op.f('ix_quotes_id'), table_name='quotes')
    op.drop_table('quotes')
    op.drop_table('action_types')
    op.drop_table('statuses')
    op.drop_table('categories')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
