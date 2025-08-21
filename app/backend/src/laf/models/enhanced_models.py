"""
Enhanced database models for scalable service architecture
"""
from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, DECIMAL, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional, List, Dict, Any

# Import the shared Base from core.database
from ..core.database import Base

# Enums
class ServiceStatus(PyEnum):
    ONLINE = "online"
    OFFLINE = "offline" 
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class QueueStatus(PyEnum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DependencyType(PyEnum):
    SEQUENTIAL = "sequential"
    CONDITIONAL = "conditional"
    RESOURCE_SHARING = "resource_sharing"

# Enhanced Service Registry
class ServiceV2(Base):
    __tablename__ = "services_v2"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)  # hplc, sample_prep, balance, etc.
    category = Column(String(100))  # analytical, preparative, storage, etc.
    endpoint = Column(String(500), nullable=False)
    status = Column(ENUM(ServiceStatus), default=ServiceStatus.OFFLINE)
    health_check_endpoint = Column(String(500))
    max_concurrent_tasks = Column(Integer, default=1)
    current_load = Column(Integer, default=0)
    priority = Column(Integer, default=5)
    location = Column(String(255))
    capabilities = Column(JSONB)  # {"hplc": True, "uv_detector": True, "autosampler": True}
    configuration = Column(JSONB)  # Service-specific configuration
    service_metadata = Column(JSONB)  # Additional metadata (renamed to avoid SQLAlchemy conflict)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    last_heartbeat = Column(TIMESTAMP)
    maintenance_window = Column(JSONB)  # {"start": "02:00", "end": "04:00", "days": ["sunday"]}
    cost_per_hour = Column(DECIMAL(10, 2))

    # Relationships
    capabilities_rel = relationship("ServiceCapability", back_populates="service", cascade="all, delete-orphan")
    performance_metrics = relationship("ServicePerformanceMetric", back_populates="service", cascade="all, delete-orphan")
    queue_entries = relationship("WorkflowExecutionQueue", back_populates="assigned_service")

    def is_available(self) -> bool:
        """Check if service is available for new tasks"""
        return (self.status == ServiceStatus.ONLINE and 
                self.current_load < self.max_concurrent_tasks)

    def get_load_percentage(self) -> float:
        """Get current load as percentage"""
        if self.max_concurrent_tasks == 0:
            return 0.0
        return (self.current_load / self.max_concurrent_tasks) * 100

# Enhanced Task Templates with Capabilities
class TaskTemplateV2(Base):
    __tablename__ = "task_templates_v2"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    description = Column(Text)
    required_capabilities = Column(JSONB, nullable=False)  # ["hplc", "uv_detector"]
    optional_capabilities = Column(JSONB, default=[])  # ["autosampler", "column_oven"]
    parameter_schema = Column(JSONB, nullable=False)  # JSON schema for parameters
    default_parameters = Column(JSONB, default={})
    estimated_duration_seconds = Column(Integer)
    complexity_score = Column(Integer, default=1)  # 1-10 scale
    resource_requirements = Column(JSONB)  # {"memory": "1GB", "cpu": 2}
    validation_rules = Column(JSONB)  # Parameter validation rules
    tags = Column(JSONB, default=[])  # Tags for categorization
    created_by = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)

    # Note: Enhanced TaskTemplate is separate from existing Task model
    # No direct relationship to avoid foreign key conflicts

    def matches_service_capabilities(self, service_capabilities: Dict[str, Any]) -> bool:
        """Check if a service has all required capabilities for this task"""
        for capability in self.required_capabilities:
            if capability not in service_capabilities:
                return False
        return True

# Service Capabilities Mapping
class ServiceCapability(Base):
    __tablename__ = "service_capabilities"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services_v2.id", ondelete="CASCADE"), nullable=False)
    capability_name = Column(String(255), nullable=False)
    capability_value = Column(JSONB)  # Additional capability metadata
    confidence_score = Column(DECIMAL(3, 2), default=1.0)  # How well service handles this capability
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    service = relationship("ServiceV2", back_populates="capabilities_rel")

# User Preferences for Service Selection
class UserServicePreference(Base):
    __tablename__ = "user_service_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False)
    task_type = Column(String(255))  # Specific task type or None for global preferences
    preferred_service_ids = Column(ARRAY(Integer))  # Ordered list of preferred services
    blacklisted_service_ids = Column(ARRAY(Integer))  # Services to avoid
    criteria = Column(JSONB)  # {"cost_weight": 0.3, "speed_weight": 0.7, "reliability_weight": 0.5}
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

# Enhanced Workflow Queue Management
class WorkflowExecutionQueue(Base):
    __tablename__ = "workflow_execution_queue"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    preferred_service_ids = Column(ARRAY(Integer))  # User's preferred services
    assigned_service_id = Column(Integer, ForeignKey("services_v2.id"))
    priority = Column(Integer, default=5)  # 1 (highest) to 10 (lowest)
    queue_position = Column(Integer)
    estimated_start_time = Column(TIMESTAMP)
    estimated_completion_time = Column(TIMESTAMP)
    actual_start_time = Column(TIMESTAMP)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=3600)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    status = Column(ENUM(QueueStatus), default=QueueStatus.PENDING)

    # Relationships
    workflow = relationship("Workflow")
    task = relationship("Task")
    assigned_service = relationship("ServiceV2", back_populates="queue_entries")

# Service Performance Metrics
class ServicePerformanceMetric(Base):
    __tablename__ = "service_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services_v2.id", ondelete="CASCADE"), nullable=False)
    task_type = Column(String(255))
    execution_count = Column(Integer, default=0)
    average_duration_seconds = Column(DECIMAL(10, 2))
    success_rate = Column(DECIMAL(5, 4))  # 0.0 to 1.0
    error_rate = Column(DECIMAL(5, 4))  # 0.0 to 1.0
    last_success_time = Column(TIMESTAMP)
    last_failure_time = Column(TIMESTAMP)
    uptime_percentage = Column(DECIMAL(5, 4))  # 0.0 to 1.0
    recorded_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    service = relationship("ServiceV2", back_populates="performance_metrics")

# Workflow Scheduling and Batching
class WorkflowSchedule(Base):
    __tablename__ = "workflow_schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    workflow_template_id = Column(Integer)  # Reference to workflow template (if using templates)
    cron_expression = Column(String(255))  # Cron expression for scheduling
    batch_size = Column(Integer, default=1)  # Number of workflows to create per trigger
    parallel_execution = Column(Boolean, default=False)  # Can workflows run in parallel
    resource_constraints = Column(JSONB)  # Resource limits for batch execution
    created_by = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=func.now())
    is_active = Column(Boolean, default=True)

# Enhanced Task Dependencies
class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    dependent_task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    prerequisite_task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    dependency_type = Column(ENUM(DependencyType), default=DependencyType.SEQUENTIAL)
    conditions = Column(JSONB)  # Conditions that must be met for dependency to be satisfied
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    workflow = relationship("Workflow")
    dependent_task = relationship("Task", foreign_keys=[dependent_task_id])
    prerequisite_task = relationship("Task", foreign_keys=[prerequisite_task_id])

# Add backward compatibility - import existing models and extend Task model
from .database import Workflow, Task, Result

# Extend existing Task model with new fields (this would be done via migration)
# These fields will be added to the existing Task model:
# - preferred_service_ids: ARRAY(Integer)
# - required_capabilities: JSONB
# - task_template_id: Integer (FK to TaskTemplate)
# - estimated_duration_seconds: Integer
# - priority: Integer
# - timeout_seconds: Integer

# Note: Removed problematic Task model monkey patches to avoid SQLAlchemy conflicts
# The enhanced models operate independently of the existing Task model