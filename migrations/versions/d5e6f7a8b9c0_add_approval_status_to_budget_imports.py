"""Add approval_status workflow columns to budget_imports (FASE MASTER).

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-06-29 00:00:00.000000

Adds four columns to budget_imports for the human-approval workflow introduced
in FASE MASTER.  The technical ingestion `status` column is unchanged.

  approval_status  — PENDING_REVIEW | APPROVED | REJECTED (never null)
  reviewed_by      — identifier of who approved/rejected (nullable)
  reviewed_at      — timestamp of the review action (nullable)
  review_notes     — optional comment, e.g. rejection reason (nullable)

Existing rows receive approval_status = 'PENDING_REVIEW' via server_default,
matching the Python-side default, so no data is invented or back-filled.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('budget_imports') as batch_op:
        batch_op.add_column(
            sa.Column(
                'approval_status',
                sa.String(length=30),
                nullable=False,
                server_default='PENDING_REVIEW',
            )
        )
        batch_op.add_column(
            sa.Column('reviewed_by', sa.String(length=255), nullable=True)
        )
        batch_op.add_column(
            sa.Column('reviewed_at', sa.DateTime(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('review_notes', sa.Text(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table('budget_imports') as batch_op:
        batch_op.drop_column('review_notes')
        batch_op.drop_column('reviewed_at')
        batch_op.drop_column('reviewed_by')
        batch_op.drop_column('approval_status')
