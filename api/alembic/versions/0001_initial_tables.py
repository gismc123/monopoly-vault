"""initial tables

Revision ID: 0001
Revises: 
Create Date: 2026-10-10 16:15:50.026635
"""
from alembic import op
import sqlalchemy as sa


revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('username', sa.String(length=40), nullable=False),
    sa.Column('password_hash', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('session_started_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('vaults',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('campaign_year', sa.Integer(), nullable=False),
    sa.Column('invite_code', sa.String(length=12), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('invite_code')
    )
    op.create_index(op.f('ix_vaults_campaign_year'), 'vaults', ['campaign_year'], unique=False)
    op.create_table('codes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code_text', sa.String(length=32), nullable=False),
    sa.Column('campaign_year', sa.Integer(), nullable=False),
    sa.Column('piece_number', sa.Integer(), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.Column('vault_id', sa.Integer(), nullable=True),
    sa.Column('visibility', sa.Enum('shared', 'private', name='visibility', native_enum=False, create_constraint=True, length=16), nullable=False),
    sa.Column('status', sa.Enum('available', 'pending', 'used', name='code_status', native_enum=False, create_constraint=True, length=16), nullable=False),
    sa.Column('photo_path', sa.String(length=255), nullable=True),
    sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('copied_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('copied_by_id', sa.Integer(), nullable=True),
    sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('used_by_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['copied_by_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['used_by_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['vault_id'], ['vaults.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('campaign_year', 'code_text', name='uq_codes_year_text')
    )
    op.create_index(op.f('ix_codes_campaign_year'), 'codes', ['campaign_year'], unique=False)
    op.create_index(op.f('ix_codes_owner_id'), 'codes', ['owner_id'], unique=False)
    op.create_index(op.f('ix_codes_vault_id'), 'codes', ['vault_id'], unique=False)
    op.create_table('vault_members',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('vault_id', sa.Integer(), nullable=False),
    sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['vault_id'], ['vaults.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'vault_id')
    )


def downgrade() -> None:
    op.drop_table('vault_members')
    op.drop_index(op.f('ix_codes_vault_id'), table_name='codes')
    op.drop_index(op.f('ix_codes_owner_id'), table_name='codes')
    op.drop_index(op.f('ix_codes_campaign_year'), table_name='codes')
    op.drop_table('codes')
    op.drop_index(op.f('ix_vaults_campaign_year'), table_name='vaults')
    op.drop_table('vaults')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
