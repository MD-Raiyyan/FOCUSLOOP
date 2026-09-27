"""0003_task_lifecycle_and_checkin_unique

Revision ID: 0003_task_lifecycle
Revises: 0002_onboarding
Create Date: 2026-09-27 14:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0003_task_lifecycle'
down_revision: Union[str, Sequence[str], None] = '0002_onboarding'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Clean up any historical frequency representations in tasks
    # Normalize nulls or legacy values to 'daily'
    conn.execute(sa.text("UPDATE tasks SET frequency = 'daily' WHERE frequency IS NULL OR frequency = '' OR frequency = 'regular';"))
    conn.execute(sa.text("UPDATE tasks SET frequency = 'once' WHERE frequency IN ('one_time', 'one-time', 'single');"))

    # 2. Deduplicate task_checkins on (task_id, date) before adding unique constraint
    conn.execute(sa.text("""
        DELETE FROM task_checkins
        WHERE id IN (
            SELECT id FROM (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY task_id, date 
                    ORDER BY created_at DESC
                ) as rnum
                FROM task_checkins
            ) t
            WHERE t.rnum > 1
        );
    """))

    # 3. Add unique constraint on task_checkins (task_id, date)
    with op.batch_alter_table('task_checkins') as batch_op:
        batch_op.create_unique_constraint('uq_task_checkin_task_date', ['task_id', 'date'])


def downgrade() -> None:
    with op.batch_alter_table('task_checkins') as batch_op:
        batch_op.drop_constraint('uq_task_checkin_task_date', type_='unique')
