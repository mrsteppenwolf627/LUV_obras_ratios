"""Add budget_imports table for JSON-API import tracking.

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-06-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'budget_imports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('building_type', sa.String(length=100), nullable=True),
        sa.Column('import_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='success'),
        sa.Column('items_count', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_hash', name='uq_budget_imports_file_hash'),
    )
    op.create_index('ix_budget_imports_file_hash', 'budget_imports', ['file_hash'], unique=True)
    op.create_index('ix_budget_imports_import_date', 'budget_imports', ['import_date'])


def downgrade() -> None:
    op.drop_index('ix_budget_imports_import_date', table_name='budget_imports')
    op.drop_index('ix_budget_imports_file_hash', table_name='budget_imports')
    op.drop_table('budget_imports')
