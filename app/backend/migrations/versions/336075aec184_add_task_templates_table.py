"""Add task_templates table

Revision ID: 336075aec184
Revises: 6d3b7f86af99
Create Date: 2025-08-17 02:59:00.489643

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '336075aec184'
down_revision: Union[str, Sequence[str], None] = '6d3b7f86af99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create task_templates table
    op.create_table(
        'task_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('type', sa.String(length=64), nullable=False),
        sa.Column('required_service_type', sa.String(length=64), nullable=True),
        sa.Column('default_parameters', sa.JSON(), nullable=True),
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_templates_id'), 'task_templates', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop task_templates table
    op.drop_index(op.f('ix_task_templates_id'), table_name='task_templates')
    op.drop_table('task_templates')
