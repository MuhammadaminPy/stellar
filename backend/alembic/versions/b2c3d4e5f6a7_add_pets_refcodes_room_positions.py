"""add pets refcodes room positions

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-25 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add ref_code and ref_code_used to users
    op.add_column('users', sa.Column('ref_code', sa.String(12), nullable=True, unique=True))
    op.add_column('users', sa.Column('ref_code_used', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('has_chosen_pet', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index('ix_users_ref_code', 'users', ['ref_code'], unique=True)

    # Update existing users with ref_code using tg_id
    op.execute("""
        UPDATE users 
        SET ref_code = UPPER(SUBSTRING(MD5(CAST(tg_id AS TEXT)), 1, 8)),
            ref_code_used = true
        WHERE ref_code IS NULL
    """)

    # Add item_positions to rooms
    op.add_column('rooms', sa.Column('item_positions', sa.Text(), nullable=True))

    # Create pets table
    op.create_table(
        'pets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('pet_type', sa.String(16), nullable=False),  # 'cat' or 'dog'
        sa.Column('name', sa.String(64), nullable=True),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('xp', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_alive', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_fed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_petted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('missed_feeds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('missed_pets', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_feeds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_pets', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.tg_id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_pets_user_id', 'pets', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_pets_user_id', table_name='pets')
    op.drop_table('pets')
    op.drop_column('rooms', 'item_positions')
    op.drop_index('ix_users_ref_code', table_name='users')
    op.drop_column('users', 'has_chosen_pet')
    op.drop_column('users', 'ref_code_used')
    op.drop_column('users', 'ref_code')
