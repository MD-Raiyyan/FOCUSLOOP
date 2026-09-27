"""0004_experiment_results_nullable_values

Revision ID: 0004_exp_results_null
Revises: 0003_task_lifecycle
Create Date: 2026-09-27 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0004_exp_results_null'
down_revision: Union[str, Sequence[str], None] = '0003_task_lifecycle'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('experiment_results') as batch_op:
        batch_op.alter_column('before_value', existing_type=sa.Float(), nullable=True)
        batch_op.alter_column('after_value', existing_type=sa.Float(), nullable=True)
        batch_op.alter_column('change_value', existing_type=sa.Float(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('experiment_results') as batch_op:
        batch_op.alter_column('before_value', existing_type=sa.Float(), nullable=False)
        batch_op.alter_column('after_value', existing_type=sa.Float(), nullable=False)
        batch_op.alter_column('change_value', existing_type=sa.Float(), nullable=False)
