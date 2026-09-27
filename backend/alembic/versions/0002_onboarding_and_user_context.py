"""0002_onboarding_and_user_context

Revision ID: 0002_onboarding
Revises: dd8e4616222a
Create Date: 2026-09-27 13:48:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0002_onboarding'
down_revision: Union[str, Sequence[str], None] = 'dd8e4616222a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add onboarding columns to users table
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default=sa.text('false')))
        batch_op.add_column(sa.Column('onboarding_completed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('onboarding_step', sa.String(length=20), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('age_range', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('gender', sa.String(length=50), nullable=True))

    # 2. Create user_goals table
    op.create_table(
        'user_goals',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_user_goals_user_id'), 'user_goals', ['user_id'], unique=False)

    # 3. Create user_routine_contexts table
    op.create_table(
        'user_routine_contexts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('preferred_time_window', sa.String(length=50), nullable=True),
        sa.Column('daily_available_duration', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_routine_context_user_id'),
    )
    op.create_index(op.f('ix_user_routine_contexts_user_id'), 'user_routine_contexts', ['user_id'], unique=True)

    # 4. Create user_challenges table
    op.create_table(
        'user_challenges',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('challenge_text', sa.String(length=200), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='self_reported'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_user_challenges_user_id'), 'user_challenges', ['user_id'], unique=False)

    # 5. Create user_interests table
    op.create_table(
        'user_interests',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('interest_text', sa.String(length=100), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='self_reported'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_user_interests_user_id'), 'user_interests', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_interests_user_id'), table_name='user_interests')
    op.drop_table('user_interests')

    op.drop_index(op.f('ix_user_challenges_user_id'), table_name='user_challenges')
    op.drop_table('user_challenges')

    op.drop_index(op.f('ix_user_routine_contexts_user_id'), table_name='user_routine_contexts')
    op.drop_table('user_routine_contexts')

    op.drop_index(op.f('ix_user_goals_user_id'), table_name='user_goals')
    op.drop_table('user_goals')

    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('gender')
        batch_op.drop_column('age_range')
        batch_op.drop_column('onboarding_step')
        batch_op.drop_column('onboarding_completed_at')
        batch_op.drop_column('onboarding_completed')
