"""
Task Scheduler - Intelligent task scheduling and queue management system
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..models.enhanced_models import (
    ServiceV2, WorkflowExecutionQueue, QueueStatus, TaskTemplateV2, 
    UserServicePreference, ServicePerformanceMetric, TaskDependency
)
from ..models.database import Workflow, Task
from .service_registry import ServiceRegistry, LoadBalancingStrategy
from .capability_matcher import CapabilityMatcher, TaskRequirements, MatchScore

logger = logging.getLogger(__name__)

class SchedulingStrategy(Enum):
    FIFO = "fifo"                    # First In, First Out
    PRIORITY = "priority"            # Priority-based scheduling
    SHORTEST_JOB_FIRST = "sjf"      # Shortest estimated duration first
    FAIR_SHARE = "fair_share"       # Fair resource allocation per user
    DEADLINE_AWARE = "deadline"     # Consider task deadlines
    COST_OPTIMIZED = "cost"         # Minimize execution costs
    LOAD_BALANCED = "load_balanced" # Balance load across services

@dataclass
class ScheduleResult:
    """Result of workflow scheduling operation"""
    workflow_id: int
    success: bool
    scheduled_tasks: int
    failed_tasks: int
    estimated_start_time: Optional[datetime] = None
    estimated_completion_time: Optional[datetime] = None
    assigned_services: Dict[int, int] = None  # task_id -> service_id
    queue_positions: Dict[int, int] = None    # task_id -> position
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.assigned_services is None:
            self.assigned_services = {}
        if self.queue_positions is None:
            self.queue_positions = {}
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

@dataclass
class ExecutionEstimate:
    """Workflow execution time and resource estimates"""
    workflow_id: int
    total_estimated_duration: timedelta
    critical_path_duration: timedelta
    earliest_start_time: datetime
    estimated_completion_time: datetime
    resource_requirements: Dict[str, Any]
    bottlenecks: List[str]
    parallelizable_tasks: List[int]
    cost_estimate: Optional[float] = None

@dataclass
class UserPreferences:
    """User scheduling preferences"""
    user_id: str
    priority_weight: float = 0.5      # How much to weight priority
    cost_weight: float = 0.3          # How much to weight cost
    speed_weight: float = 0.7         # How much to weight execution speed  
    reliability_weight: float = 0.8   # How much to weight service reliability
    preferred_services: List[int] = None
    blacklisted_services: List[int] = None
    max_wait_time: Optional[timedelta] = None
    
    def __post_init__(self):
        if self.preferred_services is None:
            self.preferred_services = []
        if self.blacklisted_services is None:
            self.blacklisted_services = []

class TaskScheduler:
    """Intelligent task scheduling and queue management"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.service_registry = ServiceRegistry(db_session)
        self.capability_matcher = CapabilityMatcher(db_session)
        self.default_strategy = SchedulingStrategy.PRIORITY
        
        # Scheduling configuration
        self.max_queue_time = timedelta(hours=24)
        self.rebalance_interval = timedelta(minutes=15)
        self.priority_boost_factor = 0.1  # Boost priority for waiting tasks
        
    async def schedule_workflow(self, 
                              workflow: Workflow,
                              user_preferences: Optional[UserPreferences] = None,
                              strategy: SchedulingStrategy = None) -> ScheduleResult:
        """Schedule entire workflow with optimization"""
        try:
            if strategy is None:
                strategy = self.default_strategy
                
            logger.info(f"Scheduling workflow {workflow.id} using strategy: {strategy}")
            
            # Get workflow tasks ordered by execution order
            tasks = self.db.query(Task).filter(
                Task.workflow_id == workflow.id
            ).order_by(Task.order_index).all()
            
            if not tasks:
                return ScheduleResult(
                    workflow_id=workflow.id,
                    success=False,
                    scheduled_tasks=0,
                    failed_tasks=0,
                    errors=["No tasks found in workflow"]
                )
            
            # Analyze task dependencies
            dependencies = self._analyze_task_dependencies(workflow.id)
            
            # Create scheduling plan
            schedule_result = ScheduleResult(
                workflow_id=workflow.id,
                success=True,
                scheduled_tasks=0,
                failed_tasks=0
            )
            
            # Schedule each task
            for task in tasks:
                task_result = await self._schedule_single_task(
                    task, user_preferences, strategy, dependencies
                )
                
                if task_result:
                    schedule_result.scheduled_tasks += 1
                    schedule_result.assigned_services[task.id] = task_result.assigned_service_id
                    schedule_result.queue_positions[task.id] = task_result.queue_position or 0
                else:
                    schedule_result.failed_tasks += 1
                    schedule_result.errors.append(f"Failed to schedule task {task.id}: {task.name}")
            
            # Calculate overall estimates
            if schedule_result.scheduled_tasks > 0:
                estimate = await self._calculate_execution_estimates(workflow, dependencies)
                schedule_result.estimated_start_time = estimate.earliest_start_time
                schedule_result.estimated_completion_time = estimate.estimated_completion_time
                
                # Update workflow status
                workflow.status = "scheduled"
                self.db.commit()
            
            schedule_result.success = schedule_result.failed_tasks == 0
            
            logger.info(f"Scheduled workflow {workflow.id}: {schedule_result.scheduled_tasks} tasks, {schedule_result.failed_tasks} failed")
            return schedule_result
            
        except Exception as e:
            logger.error(f"Failed to schedule workflow {workflow.id}: {str(e)}")
            self.db.rollback()
            return ScheduleResult(
                workflow_id=workflow.id,
                success=False,
                scheduled_tasks=0,
                failed_tasks=len(tasks) if 'tasks' in locals() else 0,
                errors=[f"Scheduling error: {str(e)}"]
            )

    async def resolve_task_service_mapping(self, 
                                         task: Task,
                                         available_services: List[ServiceV2],
                                         user_preferences: Optional[UserPreferences] = None) -> Optional[ServiceV2]:
        """Resolve which service should execute a specific task"""
        try:
            if not available_services:
                logger.warning(f"No available services for task {task.id}")
                return None
            
            # Build task requirements
            requirements = self._build_task_requirements(task)
            
            # Get capability matches
            match_scores = self.capability_matcher.match_capabilities(requirements, available_services)
            
            # Filter out incompatible services
            compatible_services = [
                score for score in match_scores 
                if score.quality.value not in ['poor', 'incompatible']
            ]
            
            if not compatible_services:
                logger.warning(f"No compatible services found for task {task.id}")
                return None
            
            # Apply user preferences if provided
            if user_preferences:
                compatible_services = self._apply_user_preferences_to_matches(
                    compatible_services, user_preferences
                )
            
            # Select best service using load balancing
            service_candidates = []
            for score in compatible_services[:5]:  # Top 5 candidates
                service = self.db.query(ServiceV2).filter(Service.id == score.service_id).first()
                if service:
                    service_candidates.append(service)
            
            if not service_candidates:
                return None
            
            # Use load balancing to select final service
            selected_service = await self.service_registry.load_balance_selection(
                service_candidates,
                LoadBalancingStrategy.LEAST_LOADED,
                {
                    'user_id': user_preferences.user_id if user_preferences else None,
                    'task_type': task.name,
                    'required_capabilities': requirements.required_capabilities,
                    'optional_capabilities': requirements.optional_capabilities
                }
            )
            
            logger.info(f"Mapped task {task.id} to service {selected_service.id} ({selected_service.name})")
            return selected_service
            
        except Exception as e:
            logger.error(f"Failed to resolve service mapping for task {task.id}: {str(e)}")
            return None

    async def estimate_execution_time(self, workflow: Workflow) -> ExecutionEstimate:
        """Provide realistic execution time estimates"""
        try:
            tasks = self.db.query(Task).filter(
                Task.workflow_id == workflow.id
            ).order_by(Task.order_index).all()
            
            dependencies = self._analyze_task_dependencies(workflow.id)
            
            return await self._calculate_execution_estimates(workflow, dependencies)
            
        except Exception as e:
            logger.error(f"Failed to estimate execution time for workflow {workflow.id}: {str(e)}")
            raise

    async def rebalance_queue(self) -> Dict[str, Any]:
        """Optimize queue based on current system state"""
        try:
            logger.info("Starting queue rebalancing")
            
            # Get all pending queue entries
            pending_entries = self.db.query(WorkflowExecutionQueue).filter(
                WorkflowExecutionQueue.status == QueueStatus.PENDING
            ).all()
            
            rebalanced = 0
            reassigned = 0
            
            for entry in pending_entries:
                # Check if originally assigned service is still optimal
                original_service = entry.assigned_service_id
                task = entry.task
                
                # Get current available services
                available_services = await self.service_registry.get_available_services()
                
                # Find optimal service with current conditions
                optimal_service = await self.resolve_task_service_mapping(
                    task, available_services
                )
                
                if optimal_service and optimal_service.id != original_service:
                    # Reassign to better service
                    entry.assigned_service_id = optimal_service.id
                    entry.updated_at = datetime.utcnow()
                    reassigned += 1
                    
                # Update queue position based on current priority and wait time
                wait_time = datetime.utcnow() - entry.created_at
                if wait_time > timedelta(hours=1):
                    # Boost priority for tasks waiting too long
                    entry.priority = max(1, entry.priority - 1)
                    rebalanced += 1
            
            self.db.commit()
            
            result = {
                "rebalanced_entries": rebalanced,
                "reassigned_entries": reassigned,
                "total_pending": len(pending_entries),
                "timestamp": datetime.utcnow()
            }
            
            logger.info(f"Queue rebalancing completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Queue rebalancing failed: {str(e)}")
            self.db.rollback()
            raise

    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status and metrics"""
        try:
            # Get queue statistics
            queue_stats = self.db.query(
                WorkflowExecutionQueue.status,
                func.count(WorkflowExecutionQueue.id).label('count'),
                func.avg(
                    func.extract('epoch', 
                        func.now() - WorkflowExecutionQueue.created_at
                    )
                ).label('avg_wait_time')
            ).group_by(WorkflowExecutionQueue.status).all()
            
            status_counts = {}
            total_entries = 0
            avg_wait_times = {}
            
            for status, count, avg_wait in queue_stats:
                status_counts[status.value] = count
                total_entries += count
                if avg_wait:
                    avg_wait_times[status.value] = float(avg_wait)
            
            # Get service load distribution
            service_loads = self.db.query(
                Service.id,
                Service.name,
                Service.current_load,
                Service.max_concurrent_tasks
            ).all()
            
            service_utilization = []
            for service_id, name, current_load, max_tasks in service_loads:
                utilization = (current_load / max_tasks) * 100 if max_tasks > 0 else 0
                service_utilization.append({
                    "service_id": service_id,
                    "service_name": name,
                    "current_load": current_load,
                    "max_tasks": max_tasks,
                    "utilization_percent": utilization
                })
            
            return {
                "total_entries": total_entries,
                "status_breakdown": status_counts,
                "average_wait_times": avg_wait_times,
                "service_utilization": service_utilization,
                "timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {str(e)}")
            raise

    # Private methods
    
    async def _schedule_single_task(self, 
                                   task: Task,
                                   user_preferences: Optional[UserPreferences],
                                   strategy: SchedulingStrategy,
                                   dependencies: Dict[int, List[int]]) -> Optional[WorkflowExecutionQueue]:
        """Schedule a single task"""
        try:
            # Get available services
            available_services = await self.service_registry.get_available_services(
                task_type=task.name,
                user_id=user_preferences.user_id if user_preferences else None
            )
            
            if not available_services:
                logger.warning(f"No available services for task {task.id}")
                return None
            
            # Resolve service mapping
            selected_service = await self.resolve_task_service_mapping(
                task, available_services, user_preferences
            )
            
            if not selected_service:
                return None
            
            # Calculate priority based on strategy
            priority = self._calculate_task_priority(task, strategy, dependencies)
            
            # Estimate execution times
            estimated_duration = self._estimate_task_duration(task, selected_service)
            estimated_start = datetime.utcnow()
            estimated_completion = estimated_start + estimated_duration
            
            # Create queue entry
            queue_entry = WorkflowExecutionQueue(
                workflow_id=task.workflow_id,
                task_id=task.id,
                preferred_service_ids=getattr(task, 'preferred_service_ids', None),
                assigned_service_id=selected_service.id,
                priority=priority,
                estimated_start_time=estimated_start,
                estimated_completion_time=estimated_completion,
                status=QueueStatus.PENDING,
                created_at=datetime.utcnow()
            )
            
            self.db.add(queue_entry)
            self.db.flush()  # Get ID
            
            # Update queue position
            queue_entry.queue_position = await self._calculate_queue_position(queue_entry)
            
            return queue_entry
            
        except Exception as e:
            logger.error(f"Failed to schedule task {task.id}: {str(e)}")
            return None

    def _analyze_task_dependencies(self, workflow_id: int) -> Dict[int, List[int]]:
        """Analyze task dependencies for a workflow"""
        dependencies = {}
        
        # Get dependency relationships
        deps = self.db.query(TaskDependency).filter(
            TaskDependency.workflow_id == workflow_id
        ).all()
        
        for dep in deps:
            if dep.dependent_task_id not in dependencies:
                dependencies[dep.dependent_task_id] = []
            dependencies[dep.dependent_task_id].append(dep.prerequisite_task_id)
        
        return dependencies

    def _build_task_requirements(self, task: Task) -> TaskRequirements:
        """Build task requirements from task information"""
        # Get task template if available
        task_template = None
        if hasattr(task, 'task_template_id') and task.task_template_id:
            task_template = self.db.query(TaskTemplateV2).filter(
                TaskTemplateV2.id == task.task_template_id
            ).first()
        
        if task_template:
            return TaskRequirements(
                task_type=task.name,
                required_capabilities=task_template.required_capabilities or [],
                optional_capabilities=task_template.optional_capabilities or [],
                resource_requirements=task_template.resource_requirements or {},
                performance_requirements={},
                constraints={}
            )
        else:
            # Infer requirements from task name/type
            return self._infer_task_requirements(task)

    def _infer_task_requirements(self, task: Task) -> TaskRequirements:
        """Infer task requirements from task name/type when no template available"""
        task_name_lower = task.name.lower()
        
        # Basic capability inference
        required_caps = []
        optional_caps = []
        
        if 'hplc' in task_name_lower:
            required_caps.extend(['hplc', 'uv_detector'])
            optional_caps.extend(['autosampler', 'column_oven'])
        elif 'sample' in task_name_lower and 'prep' in task_name_lower:
            required_caps.extend(['balance', 'pipette'])
            optional_caps.extend(['ph_measurement', 'heating', 'cooling'])
        elif 'balance' in task_name_lower or 'weigh' in task_name_lower:
            required_caps.append('balance')
        
        return TaskRequirements(
            task_type=task.name,
            required_capabilities=required_caps,
            optional_capabilities=optional_caps
        )

    def _apply_user_preferences_to_matches(self, 
                                         match_scores: List[MatchScore],
                                         preferences: UserPreferences) -> List[MatchScore]:
        """Apply user preferences to capability match scores"""
        # Filter out blacklisted services
        if preferences.blacklisted_services:
            match_scores = [
                score for score in match_scores 
                if score.service_id not in preferences.blacklisted_services
            ]
        
        # Boost preferred services
        if preferences.preferred_services:
            for score in match_scores:
                if score.service_id in preferences.preferred_services:
                    preference_index = preferences.preferred_services.index(score.service_id)
                    boost = (len(preferences.preferred_services) - preference_index) * 0.1
                    score.score = min(1.0, score.score + boost)
        
        # Re-sort by updated scores
        match_scores.sort(key=lambda x: x.score, reverse=True)
        return match_scores

    def _calculate_task_priority(self, 
                               task: Task,
                               strategy: SchedulingStrategy,
                               dependencies: Dict[int, List[int]]) -> int:
        """Calculate task priority based on scheduling strategy"""
        base_priority = getattr(task, 'priority', 5)
        
        if strategy == SchedulingStrategy.PRIORITY:
            return base_priority
        
        elif strategy == SchedulingStrategy.SHORTEST_JOB_FIRST:
            # Lower duration = higher priority (lower number)
            estimated_duration = getattr(task, 'estimated_duration_seconds', 3600)
            return max(1, min(10, int(estimated_duration / 600)))  # 10 min buckets
        
        elif strategy == SchedulingStrategy.DEADLINE_AWARE:
            # Check if task has deadline in service_parameters
            if task.service_parameters and 'deadline' in task.service_parameters:
                # Calculate urgency based on deadline
                deadline = datetime.fromisoformat(task.service_parameters['deadline'])
                time_to_deadline = (deadline - datetime.utcnow()).total_seconds()
                if time_to_deadline < 3600:  # Less than 1 hour
                    return 1  # Highest priority
                elif time_to_deadline < 86400:  # Less than 1 day
                    return 2
                else:
                    return base_priority
            return base_priority
        
        elif strategy == SchedulingStrategy.FAIR_SHARE:
            # This would require tracking user resource usage
            # For now, use base priority
            return base_priority
        
        else:
            return base_priority

    def _estimate_task_duration(self, task: Task, service: Service) -> timedelta:
        """Estimate task execution duration on specific service"""
        # Check if task has estimated duration
        if hasattr(task, 'estimated_duration_seconds') and task.estimated_duration_seconds:
            base_duration = task.estimated_duration_seconds
        else:
            # Get from task template
            if hasattr(task, 'task_template_id') and task.task_template_id:
                template = self.db.query(TaskTemplateV2).filter(
                    TaskTemplateV2.id == task.task_template_id
                ).first()
                base_duration = template.estimated_duration_seconds if template else 3600
            else:
                base_duration = 3600  # Default 1 hour
        
        # Adjust based on service performance
        perf_metric = self.db.query(ServicePerformanceMetric).filter(
            ServicePerformanceMetric.service_id == service.id,
            ServicePerformanceMetric.task_type == task.name
        ).order_by(ServicePerformanceMetric.recorded_at.desc()).first()
        
        if perf_metric and perf_metric.average_duration_seconds:
            # Use historical average, but cap the adjustment
            historical_duration = float(perf_metric.average_duration_seconds)
            adjustment_factor = min(2.0, max(0.5, historical_duration / base_duration))
            base_duration = int(base_duration * adjustment_factor)
        
        return timedelta(seconds=base_duration)

    async def _calculate_queue_position(self, queue_entry: WorkflowExecutionQueue) -> int:
        """Calculate position in queue for the task"""
        # Count tasks with higher priority or earlier creation time
        higher_priority_count = self.db.query(func.count(WorkflowExecutionQueue.id)).filter(
            and_(
                WorkflowExecutionQueue.assigned_service_id == queue_entry.assigned_service_id,
                WorkflowExecutionQueue.status == QueueStatus.PENDING,
                or_(
                    WorkflowExecutionQueue.priority < queue_entry.priority,
                    and_(
                        WorkflowExecutionQueue.priority == queue_entry.priority,
                        WorkflowExecutionQueue.created_at < queue_entry.created_at
                    )
                )
            )
        ).scalar()
        
        return (higher_priority_count or 0) + 1

    async def _calculate_execution_estimates(self, 
                                           workflow: Workflow,
                                           dependencies: Dict[int, List[int]]) -> ExecutionEstimate:
        """Calculate comprehensive execution estimates for workflow"""
        tasks = self.db.query(Task).filter(
            Task.workflow_id == workflow.id
        ).order_by(Task.order_index).all()
        
        if not tasks:
            return ExecutionEstimate(
                workflow_id=workflow.id,
                total_estimated_duration=timedelta(0),
                critical_path_duration=timedelta(0),
                earliest_start_time=datetime.utcnow(),
                estimated_completion_time=datetime.utcnow(),
                resource_requirements={},
                bottlenecks=[],
                parallelizable_tasks=[]
            )
        
        # Build task duration estimates
        task_durations = {}
        for task in tasks:
            # Get assigned service or estimate with best available service
            queue_entry = self.db.query(WorkflowExecutionQueue).filter(
                WorkflowExecutionQueue.task_id == task.id
            ).first()
            
            if queue_entry and queue_entry.assigned_service_id:
                service = self.db.query(ServiceV2).filter(
                    Service.id == queue_entry.assigned_service_id
                ).first()
            else:
                # Use first available service for estimation
                available_services = await self.service_registry.get_available_services()
                service = available_services[0] if available_services else None
            
            if service:
                duration = self._estimate_task_duration(task, service)
            else:
                duration = timedelta(hours=1)  # Default estimate
            
            task_durations[task.id] = duration
        
        # Calculate critical path (simplified)
        total_duration = sum(task_durations.values(), timedelta())
        critical_path = total_duration  # Simplified - assume sequential
        
        # Find parallelizable tasks (tasks with no dependencies)
        parallelizable = []
        for task in tasks:
            if task.id not in dependencies or not dependencies[task.id]:
                parallelizable.append(task.id)
        
        earliest_start = datetime.utcnow()
        estimated_completion = earliest_start + critical_path
        
        return ExecutionEstimate(
            workflow_id=workflow.id,
            total_estimated_duration=total_duration,
            critical_path_duration=critical_path,
            earliest_start_time=earliest_start,
            estimated_completion_time=estimated_completion,
            resource_requirements={},
            bottlenecks=[],
            parallelizable_tasks=parallelizable
        )