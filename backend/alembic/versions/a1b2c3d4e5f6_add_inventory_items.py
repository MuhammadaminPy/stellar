"""add inventory_items table

Revision ID: a1b2c3d4e5f6
Revises: 2bd2d444f7d3
Create Date: 2026-04-23 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '2bd2d444f7d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'inventory_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('serial_uid', sa.String(length=32), nullable=False),
        sa.Column('serial_number', sa.Integer(), nullable=False),
        sa.Column('inventory_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['items.id']),
        sa.ForeignKeyConstraint(['inventory_id'], ['inventories.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('serial_uid'),
    )
    op.create_index(op.f('ix_inventory_items_item_id'), 'inventory_items', ['item_id'], unique=False)
    op.create_index(op.f('ix_inventory_items_serial_uid'), 'inventory_items', ['serial_uid'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_inventory_items_serial_uid'), table_name='inventory_items')
    op.drop_index(op.f('ix_inventory_items_item_id'), table_name='inventory_items')
    op.drop_table('inventory_items')