"""Add item categories and ItemMasterRatio table.

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-06-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'item_master_ratios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_master_id', sa.Integer(), nullable=False),
        sa.Column('categoria', sa.String(length=20), nullable=False),
        sa.Column('ratio_actual', sa.Float(), nullable=True),
        sa.Column('mediana', sa.Float(), nullable=True),
        sa.Column('min_valor', sa.Float(), nullable=True),
        sa.Column('max_valor', sa.Float(), nullable=True),
        sa.Column('desv_std', sa.Float(), nullable=True),
        sa.Column('percentil_25', sa.Float(), nullable=True),
        sa.Column('percentil_75', sa.Float(), nullable=True),
        sa.Column('muestras_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('confianza', sa.String(length=20), nullable=False, server_default='MUY_DÉBIL'),
        sa.Column('ultima_actualizacion', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['item_master_id'], ['item_master.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('item_master_id', 'categoria', name='uq_item_cat_ratio'),
    )
    op.create_index('ix_item_master_ratios_item_master_id', 'item_master_ratios', ['item_master_id'])
    op.create_index('ix_item_master_ratios_categoria', 'item_master_ratios', ['categoria'])

    op.add_column('item_master', sa.Column('categoria_asignada', sa.String(length=20), nullable=False, server_default='MEDIUM'))

    op.add_column('item_instance', sa.Column('categoria_asignada', sa.String(length=20), nullable=False, server_default='MEDIUM'))
    op.add_column('item_instance', sa.Column('ratio_comparativa', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('item_instance', 'ratio_comparativa')
    op.drop_column('item_instance', 'categoria_asignada')
    op.drop_column('item_master', 'categoria_asignada')
    op.drop_index('ix_item_master_ratios_categoria', table_name='item_master_ratios')
    op.drop_index('ix_item_master_ratios_item_master_id', table_name='item_master_ratios')
    op.drop_table('item_master_ratios')
