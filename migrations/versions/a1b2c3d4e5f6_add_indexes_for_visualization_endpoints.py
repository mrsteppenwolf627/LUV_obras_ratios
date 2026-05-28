"""Add indexes for visualization endpoints

Revision ID: a1b2c3d4e5f6
Revises: 54ca4f3a91d5
Create Date: 2026-05-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '54ca4f3a91d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_line_items_chapter_code', 'line_items', ['chapter_code'], if_not_exists=True)
    op.create_index('ix_ratios_chapter_code', 'ratios', ['chapter_code'], if_not_exists=True)
    op.create_index('ix_line_items_validation_status', 'line_items', ['validation_status'], if_not_exists=True)
    op.create_index('ix_line_items_budget_id', 'line_items', ['budget_id'], if_not_exists=True)


def downgrade() -> None:
    op.drop_index('ix_line_items_budget_id', table_name='line_items')
    op.drop_index('ix_line_items_validation_status', table_name='line_items')
    op.drop_index('ix_ratios_chapter_code', table_name='ratios')
    op.drop_index('ix_line_items_chapter_code', table_name='line_items')
