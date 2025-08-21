"""Add manual completion tracking to tasks

Revision ID: add_manual_completion
Revises: 336075aec184
Create Date: 2025-08-21 04:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_manual_completion'
down_revision: Union[str, Sequence[str], None] = '336075aec184'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add manual completion tracking fields to tasks table
    op.add_column('tasks', sa.Column('manual_completion', sa.Boolean(), nullable=True, default=False))
    op.add_column('tasks', sa.Column('completed_by', sa.String(length=128), nullable=True))
    op.add_column('tasks', sa.Column('completion_method', sa.String(length=64), nullable=True, default='automatic'))
    op.add_column('tasks', sa.Column('completion_timestamp', sa.DateTime(), nullable=True))
    op.add_column('tasks', sa.Column('task_type', sa.String(length=64), nullable=True, default='automatic'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove manual completion tracking fields from tasks table
    op.drop_column('tasks', 'task_type')
    op.drop_column('tasks', 'completion_timestamp')
    op.drop_column('tasks', 'completion_method')
    op.drop_column('tasks', 'completed_by')
    op.drop_column('tasks', 'manual_completion')