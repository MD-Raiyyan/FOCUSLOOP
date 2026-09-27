"""0005_pattern_contract_and_experiment_snapshot

Revision ID: 0005_pattern_contract
Revises: 0004_exp_results_null
Create Date: 2026-09-27 22:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0005_pattern_contract'
down_revision: Union[str, Sequence[str], None] = '0004_exp_results_null'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add last_evaluated_at column to behavior_patterns
    op.add_column('behavior_patterns', sa.Column('last_evaluated_at', sa.DateTime(), nullable=True))

    # 2. Add UNIQUE constraint on (user_id, pattern_type) to behavior_patterns
    op.create_unique_constraint(
        'uq_behavior_patterns_user_pattern_type',
        'behavior_patterns',
        ['user_id', 'pattern_type']
    )

    # 3. Add pattern_snapshot JSON column to experiments
    op.add_column('experiments', sa.Column('pattern_snapshot', sa.JSON(), nullable=True))


def downgrade() -> None:
    # 1. Drop pattern_snapshot from experiments
    op.drop_column('experiments', 'pattern_snapshot')

    # 2. Drop unique constraint from behavior_patterns
    op.drop_constraint('uq_behavior_patterns_user_pattern_type', 'behavior_patterns', type_='unique')

    # 3. Drop last_evaluated_at from behavior_patterns
    op.drop_column('behavior_patterns', 'last_evaluated_at')
