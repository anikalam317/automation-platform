"""
Enhanced Pydantic schemas for the advanced service architecture
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum

from ..models.enhanced_models import ServiceStatus, QueueStatus

# Service Management Schemas

class ServiceBase(BaseModel):
    """Base service schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Service name")
    type: str = Field(..., description="Service type (hplc, sample_prep, balance, etc.)")
    category: str = Field(..., description="Service category (analytical, preparative, etc.)")
    endpoint: str = Field(..., description="Service HTTP endpoint URL")
    health_check_endpoint: Optional[str] = Field(None, description="Health check endpoint")
    max_concurrent_tasks: int = Field(1, ge=1, le=100, description="Maximum concurrent tasks")
    priority: int = Field(5, ge=1, le=10, description="Service priority (1=highest)")
    location: Optional[str] = Field(None, max_length=255, description="Physical location")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="Service capabilities")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Service configuration")
    service_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    cost_per_hour: Optional[float] = Field(None, ge=0, description="Cost per hour in USD")

class ServiceCreate(ServiceBase):
    """Schema for creating a new service"""
    pass

class ServiceUpdate(BaseModel):
    """Schema for updating a service"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = None
    category: Optional[str] = None
    endpoint: Optional[str] = None
    health_check_endpoint: Optional[str] = None
    max_concurrent_tasks: Optional[int] = Field(None, ge=1, le=100)
    priority: Optional[int] = Field(None, ge=1, le=10)
    location: Optional[str] = Field(None, max_length=255)
    capabilities: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    service_metadata: Optional[Dict[str, Any]] = None
    cost_per_hour: Optional[float] = Field(None, ge=0)

class ServiceResponse(ServiceBase):
    """Schema for service response"""
    id: int
    status: ServiceStatus
    current_load: int
    last_heartbeat: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Health and Metrics Schemas

class ServiceHealthResponse(BaseModel):
    """Service health check response"""
    service_id: int
    service_name: str
    status: ServiceStatus
    last_heartbeat: Optional[datetime]
    response_time_ms: Optional[float]
    error_message: Optional[str] = None
    current_load: int
    max_concurrent_tasks: int
    load_percentage: float

class LoadMetricsResponse(BaseModel):
    """Service load metrics response"""
    service_id: int
    current_load: int
    max_concurrent_tasks: int
    load_percentage: float
    average_response_time: float
    success_rate: float
    uptime_percentage: float
    timestamp: datetime

# Service Discovery Schemas

class TaskRequirementsSchema(BaseModel):
    """Task requirements for service discovery"""
    task_type: str = Field(..., description="Type of task")
    required_capabilities: List[str] = Field(..., description="Must-have capabilities")
    optional_capabilities: List[str] = Field(default_factory=list, description="Nice-to-have capabilities")
    resource_requirements: Dict[str, Any] = Field(default_factory=dict, description="Resource requirements")
    performance_requirements: Dict[str, Any] = Field(default_factory=dict, description="Performance requirements")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Additional constraints")

class ServiceDiscoveryRequest(BaseModel):
    """Service discovery request"""
    task_type: str = Field(..., description="Type of task to execute")
    required_capabilities: List[str] = Field(..., description="Required capabilities")
    optional_capabilities: Optional[List[str]] = Field(None, description="Optional capabilities")
    resource_requirements: Optional[Dict[str, Any]] = Field(None, description="Resource requirements")
    performance_requirements: Optional[Dict[str, Any]] = Field(None, description="Performance requirements")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Constraints")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")

class DiscoveredService(BaseModel):
    """Individual discovered service in response"""
    service_id: int
    service_name: str
    service_type: str
    category: str
    endpoint: str
    status: ServiceStatus
    current_load: int
    max_concurrent_tasks: int
    match_quality: str
    match_score: float
    required_match_rate: float
    optional_match_rate: float
    confidence: float
    reasons: List[str]
    cost_per_hour: Optional[float]

class ServiceDiscoveryResponse(BaseModel):
    """Service discovery response"""
    task_type: str
    discovered_services: List[DiscoveredService]
    total_matches: int
    discovery_time: datetime
    recommendations: List[str]

# Task Template Schemas

class TaskTemplateBase(BaseModel):
    """Base task template schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: str = Field(..., description="Template category")
    required_capabilities: List[str] = Field(default_factory=list, description="Required capabilities")
    optional_capabilities: List[str] = Field(default_factory=list, description="Optional capabilities")
    default_parameters: Dict[str, Any] = Field(default_factory=dict, description="Default parameters")
    parameter_schema: Dict[str, Any] = Field(default_factory=dict, description="Parameter validation schema")
    estimated_duration_seconds: int = Field(3600, ge=1, description="Estimated duration in seconds")
    resource_requirements: Dict[str, Any] = Field(default_factory=dict, description="Resource requirements")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")

class TaskTemplateCreate(TaskTemplateBase):
    """Schema for creating task template"""
    pass

class TaskTemplateUpdate(BaseModel):
    """Schema for updating task template"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    required_capabilities: Optional[List[str]] = None
    optional_capabilities: Optional[List[str]] = None
    default_parameters: Optional[Dict[str, Any]] = None
    parameter_schema: Optional[Dict[str, Any]] = None
    estimated_duration_seconds: Optional[int] = Field(None, ge=1)
    resource_requirements: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

class TaskTemplateResponse(TaskTemplateBase):
    """Schema for task template response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Queue Management Schemas

class QueueEntryResponse(BaseModel):
    """Queue entry response schema"""
    id: int
    workflow_id: int
    task_id: int
    preferred_service_ids: Optional[List[int]]
    assigned_service_id: Optional[int]
    priority: int
    estimated_start_time: Optional[datetime]
    estimated_completion_time: Optional[datetime]
    actual_start_time: Optional[datetime]
    actual_completion_time: Optional[datetime]
    status: QueueStatus
    queue_position: Optional[int]
    retry_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class QueueStatusResponse(BaseModel):
    """Queue status response"""
    total_entries: int
    status_breakdown: Dict[str, int]
    average_wait_times: Dict[str, float]
    service_utilization: List[Dict[str, Any]]
    timestamp: datetime

class WorkflowScheduleRequest(BaseModel):
    """Workflow scheduling request"""
    workflow_id: int
    strategy: str = Field("priority", description="Scheduling strategy")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    execution_mode: Optional[str] = Field("optimized", description="Execution mode")

class WorkflowScheduleResponse(BaseModel):
    """Workflow scheduling response"""
    workflow_id: int
    success: bool
    scheduled_tasks: int
    failed_tasks: int
    estimated_start_time: Optional[datetime]
    estimated_completion_time: Optional[datetime]
    assigned_services: Dict[int, int]  # task_id -> service_id
    queue_positions: Dict[int, int]    # task_id -> position
    errors: List[str]
    warnings: List[str]

# User Preferences Schemas

class UserServicePreferenceBase(BaseModel):
    """Base user preference schema"""
    user_id: str = Field(..., description="User identifier")
    task_type: Optional[str] = Field(None, description="Specific task type (null for global)")
    preferred_service_ids: List[int] = Field(default_factory=list, description="Preferred services in order")
    blacklisted_service_ids: List[int] = Field(default_factory=list, description="Services to avoid")
    priority_weight: float = Field(0.5, ge=0, le=1, description="Priority weight")
    cost_weight: float = Field(0.3, ge=0, le=1, description="Cost weight")
    speed_weight: float = Field(0.7, ge=0, le=1, description="Speed weight")
    reliability_weight: float = Field(0.8, ge=0, le=1, description="Reliability weight")
    max_wait_time_seconds: Optional[int] = Field(None, ge=1, description="Maximum acceptable wait time")

class UserServicePreferenceCreate(UserServicePreferenceBase):
    """Schema for creating user preferences"""
    pass

class UserServicePreferenceUpdate(BaseModel):
    """Schema for updating user preferences"""
    preferred_service_ids: Optional[List[int]] = None
    blacklisted_service_ids: Optional[List[int]] = None
    priority_weight: Optional[float] = Field(None, ge=0, le=1)
    cost_weight: Optional[float] = Field(None, ge=0, le=1)
    speed_weight: Optional[float] = Field(None, ge=0, le=1)
    reliability_weight: Optional[float] = Field(None, ge=0, le=1)
    max_wait_time_seconds: Optional[int] = Field(None, ge=1)

class UserServicePreferenceResponse(UserServicePreferenceBase):
    """Schema for user preference response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Analytics and Monitoring Schemas

class ServicePerformanceMetricResponse(BaseModel):
    """Service performance metrics response"""
    id: int
    service_id: int
    task_type: Optional[str]
    average_duration_seconds: Optional[float]
    success_rate: Optional[float]
    uptime_percentage: Optional[float]
    error_count: int
    total_executions: int
    recorded_at: datetime
    
    class Config:
        from_attributes = True

class SystemMetricsResponse(BaseModel):
    """System-wide metrics response"""
    total_services: int
    online_services: int
    total_workflows: int
    active_workflows: int
    queue_length: int
    average_wait_time_minutes: float
    system_utilization_percentage: float
    timestamp: datetime

# Workflow Execution Schemas

class ExecutionResultResponse(BaseModel):
    """Workflow execution result response"""
    workflow_id: int
    success: bool
    completed_tasks: int
    failed_tasks: int
    total_duration_seconds: float
    start_time: datetime
    end_time: datetime
    task_results: Dict[int, Any]
    errors: List[str]
    warnings: List[str]

class BatchExecutionRequest(BaseModel):
    """Batch workflow execution request"""
    workflow_ids: List[int] = Field(..., min_items=1, description="Workflow IDs to execute")
    optimization_strategy: str = Field("throughput", description="Optimization strategy")
    max_concurrent: int = Field(5, ge=1, le=20, description="Maximum concurrent workflows")

class BatchExecutionResponse(BaseModel):
    """Batch workflow execution response"""
    total_workflows: int
    successful_workflows: int
    failed_workflows: int
    total_duration_seconds: float
    throughput_workflows_per_hour: float
    workflow_results: List[ExecutionResultResponse]

# Validation and Error Schemas

class ValidationError(BaseModel):
    """Validation error details"""
    field: str
    message: str
    code: Optional[str] = None

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    validation_errors: Optional[List[ValidationError]] = None
    timestamp: datetime

# Configuration Schemas

class SystemConfigResponse(BaseModel):
    """System configuration response"""
    max_concurrent_workflows: int
    default_task_timeout_seconds: int
    health_check_interval_seconds: int
    queue_rebalance_interval_seconds: int
    service_registry_settings: Dict[str, Any]
    load_balancing_strategy: str
    recovery_strategy: str

# Custom Validators

from pydantic import validator

# Note: In Pydantic v2, validators are applied differently
# These are included in the model classes directly