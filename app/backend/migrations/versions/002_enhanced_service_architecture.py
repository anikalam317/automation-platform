"""Enhanced service architecture for scalability

Revision ID: 002_enhanced_service_architecture
Revises: 001_initial_migration
Create Date: 2025-08-20 17:45:00.000000

This migration introduces the enhanced service architecture to support:
- Dynamic service registry and discovery
- Capability-based task-to-service mapping
- Advanced queue management and load balancing
- User preferences and service selection
- Performance monitoring and analytics
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_enhanced_service_architecture'
down_revision = '001_initial_migration'
branch_labels = None
depends_on = None

def upgrade():
    # Create enums
    op.execute("CREATE TYPE service_status AS ENUM ('online', 'offline', 'busy', 'maintenance', 'error')")
    op.execute("CREATE TYPE queue_status AS ENUM ('pending', 'assigned', 'running', 'completed', 'failed', 'cancelled')")
    op.execute("CREATE TYPE dependency_type AS ENUM ('sequential', 'conditional', 'resource_sharing')")

    # Enhanced Service Registry
    op.create_table('services_v2',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('endpoint', sa.String(500), nullable=False),
        sa.Column('status', postgresql.ENUM('online', 'offline', 'busy', 'maintenance', 'error', name='service_status'), 
                  server_default='offline', nullable=True),
        sa.Column('health_check_endpoint', sa.String(500), nullable=True),
        sa.Column('max_concurrent_tasks', sa.Integer(), server_default='1', nullable=True),
        sa.Column('current_load', sa.Integer(), server_default='0', nullable=True),
        sa.Column('priority', sa.Integer(), server_default='5', nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('capabilities', postgresql.JSONB(), nullable=True),
        sa.Column('configuration', postgresql.JSONB(), nullable=True),
        sa.Column('service_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('last_heartbeat', sa.TIMESTAMP(), nullable=True),
        sa.Column('maintenance_window', postgresql.JSONB(), nullable=True),
        sa.Column('cost_per_hour', sa.DECIMAL(10,2), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_services_status', 'services_v2', ['status'])
    op.create_index('idx_services_type_category', 'services_v2', ['type', 'category'])
    op.create_index('idx_services_capabilities', 'services_v2', ['capabilities'], postgresql_using='gin')

    # Enhanced Task Templates with Capabilities  
    op.create_table('task_templates_v2',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('required_capabilities', postgresql.JSONB(), nullable=False),
        sa.Column('optional_capabilities', postgresql.JSONB(), server_default="'[]'::jsonb", nullable=True),
        sa.Column('parameter_schema', postgresql.JSONB(), nullable=False),
        sa.Column('default_parameters', postgresql.JSONB(), server_default="'{}'::jsonb", nullable=True),
        sa.Column('estimated_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('complexity_score', sa.Integer(), server_default='1', nullable=True),
        sa.Column('resource_requirements', postgresql.JSONB(), nullable=True),
        sa.Column('validation_rules', postgresql.JSONB(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_task_templates_category', 'task_templates_v2', ['category'])
    op.create_index('idx_task_templates_capabilities', 'task_templates_v2', ['required_capabilities'], postgresql_using='gin')
    op.create_index('idx_task_templates_active', 'task_templates_v2', ['is_active'])

    # Service Capabilities Mapping
    op.create_table('service_capabilities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('capability_name', sa.String(255), nullable=False),
        sa.Column('capability_value', postgresql.JSONB(), nullable=True),
        sa.Column('confidence_score', sa.DECIMAL(3,2), server_default='1.0', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['service_id'], ['services_v2.id'], ondelete='CASCADE')
    )
    op.create_index('idx_service_capabilities_service_id', 'service_capabilities', ['service_id'])
    op.create_index('idx_service_capabilities_name', 'service_capabilities', ['capability_name'])

    # User Preferences for Service Selection
    op.create_table('user_service_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('task_type', sa.String(255), nullable=True),
        sa.Column('preferred_service_ids', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('blacklisted_service_ids', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('criteria', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_preferences_user_id', 'user_service_preferences', ['user_id'])
    op.create_index('idx_user_preferences_task_type', 'user_service_preferences', ['task_type'])

    # Enhanced Workflow Queue Management
    op.create_table('workflow_execution_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('preferred_service_ids', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('assigned_service_id', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='5', nullable=True),
        sa.Column('queue_position', sa.Integer(), nullable=True),
        sa.Column('estimated_start_time', sa.TIMESTAMP(), nullable=True),
        sa.Column('estimated_completion_time', sa.TIMESTAMP(), nullable=True),
        sa.Column('actual_start_time', sa.TIMESTAMP(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('max_retries', sa.Integer(), server_default='3', nullable=True),
        sa.Column('timeout_seconds', sa.Integer(), server_default='3600', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'assigned', 'running', 'completed', 'failed', 'cancelled', name='queue_status'), 
                  server_default='pending', nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_service_id'], ['services_v2.id'])
    )
    op.create_index('idx_queue_status_priority', 'workflow_execution_queue', ['status', 'priority'])
    op.create_index('idx_queue_workflow_id', 'workflow_execution_queue', ['workflow_id'])
    op.create_index('idx_queue_assigned_service', 'workflow_execution_queue', ['assigned_service_id'])

    # Service Performance Metrics
    op.create_table('service_performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('task_type', sa.String(255), nullable=True),
        sa.Column('execution_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('average_duration_seconds', sa.DECIMAL(10,2), nullable=True),
        sa.Column('success_rate', sa.DECIMAL(5,4), nullable=True),
        sa.Column('error_rate', sa.DECIMAL(5,4), nullable=True),
        sa.Column('last_success_time', sa.TIMESTAMP(), nullable=True),
        sa.Column('last_failure_time', sa.TIMESTAMP(), nullable=True),
        sa.Column('uptime_percentage', sa.DECIMAL(5,4), nullable=True),
        sa.Column('recorded_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['service_id'], ['services_v2.id'], ondelete='CASCADE')
    )
    op.create_index('idx_performance_service_id', 'service_performance_metrics', ['service_id'])
    op.create_index('idx_performance_task_type', 'service_performance_metrics', ['task_type'])
    op.create_index('idx_performance_recorded_at', 'service_performance_metrics', ['recorded_at'])

    # Workflow Scheduling and Batching
    op.create_table('workflow_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('workflow_template_id', sa.Integer(), nullable=True),
        sa.Column('cron_expression', sa.String(255), nullable=True),
        sa.Column('batch_size', sa.Integer(), server_default='1', nullable=True),
        sa.Column('parallel_execution', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('resource_constraints', postgresql.JSONB(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_schedules_active', 'workflow_schedules', ['is_active'])

    # Enhanced Task Dependencies
    op.create_table('task_dependencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('dependent_task_id', sa.Integer(), nullable=False),
        sa.Column('prerequisite_task_id', sa.Integer(), nullable=False),
        sa.Column('dependency_type', postgresql.ENUM('sequential', 'conditional', 'resource_sharing', name='dependency_type'), 
                  server_default='sequential', nullable=True),
        sa.Column('conditions', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dependent_task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prerequisite_task_id'], ['tasks.id'], ondelete='CASCADE')
    )
    op.create_index('idx_dependencies_workflow_id', 'task_dependencies', ['workflow_id'])
    op.create_index('idx_dependencies_dependent_task', 'task_dependencies', ['dependent_task_id'])

    # Add new columns to existing tasks table for enhanced functionality
    op.add_column('tasks', sa.Column('preferred_service_ids', postgresql.ARRAY(sa.Integer()), nullable=True))
    op.add_column('tasks', sa.Column('required_capabilities', postgresql.JSONB(), nullable=True))
    op.add_column('tasks', sa.Column('task_template_id', sa.Integer(), nullable=True))
    op.add_column('tasks', sa.Column('estimated_duration_seconds', sa.Integer(), nullable=True))
    op.add_column('tasks', sa.Column('priority', sa.Integer(), server_default='5', nullable=True))
    op.add_column('tasks', sa.Column('timeout_seconds', sa.Integer(), server_default='3600', nullable=True))

    # Add foreign key constraint for task_template_id
    op.create_foreign_key('fk_tasks_task_template_id', 'tasks', 'task_templates', ['task_template_id'], ['id'])

    # Create indexes for new task columns
    op.create_index('idx_tasks_template_id', 'tasks', ['task_template_id'])
    op.create_index('idx_tasks_capabilities', 'tasks', ['required_capabilities'], postgresql_using='gin')
    op.create_index('idx_tasks_priority', 'tasks', ['priority'])

def downgrade():
    # Drop new columns from tasks table
    op.drop_index('idx_tasks_priority', table_name='tasks')
    op.drop_index('idx_tasks_capabilities', table_name='tasks')
    op.drop_index('idx_tasks_template_id', table_name='tasks')
    op.drop_constraint('fk_tasks_task_template_id', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'timeout_seconds')
    op.drop_column('tasks', 'priority')
    op.drop_column('tasks', 'estimated_duration_seconds')
    op.drop_column('tasks', 'task_template_id')
    op.drop_column('tasks', 'required_capabilities')
    op.drop_column('tasks', 'preferred_service_ids')

    # Drop tables in reverse order
    op.drop_table('task_dependencies')
    op.drop_table('workflow_schedules')
    op.drop_table('service_performance_metrics')
    op.drop_table('workflow_execution_queue')
    op.drop_table('user_service_preferences')
    op.drop_table('service_capabilities')
    op.drop_table('task_templates')
    op.drop_table('services')

    # Drop enums
    op.execute("DROP TYPE dependency_type")
    op.execute("DROP TYPE queue_status")  
    op.execute("DROP TYPE service_status")