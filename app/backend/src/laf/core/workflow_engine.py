"""
Enhanced Workflow Engine - Advanced workflow execution with dynamic routing
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.enhanced_models import (
    ServiceV2, WorkflowExecutionQueue, QueueStatus, TaskDependency,
    ServicePerformanceMetric
)
from ..models.database import Workflow, Task, Result
from .service_registry import ServiceRegistry
from .task_scheduler import TaskScheduler, UserPreferences
from .capability_matcher import CapabilityMatcher

logger = logging.getLogger(__name__)

class ExecutionMode(Enum):
    SEQUENTIAL = "sequential"      # Execute tasks one after another
    PARALLEL = "parallel"          # Execute independent tasks in parallel  
    OPTIMIZED = "optimized"       # Smart execution based on dependencies and resources
    BATCH = "batch"               # Batch multiple workflows together

class RecoveryStrategy(Enum):
    FAIL_FAST = "fail_fast"       # Stop on first failure
    CONTINUE = "continue"         # Continue with remaining tasks
    RETRY = "retry"               # Retry failed tasks
    FALLBACK = "fallback"         # Use alternative services

@dataclass
class ExecutionResult:
    """Result of workflow execution"""
    workflow_id: int
    success: bool
    completed_tasks: int
    failed_tasks: int
    total_duration: timedelta
    start_time: datetime
    end_time: datetime
    task_results: Dict[int, Any] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.task_results is None:
            self.task_results = {}
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

@dataclass
class BatchResult:
    """Result of batch workflow execution"""
    total_workflows: int
    successful_workflows: int
    failed_workflows: int
    total_duration: timedelta
    throughput: float  # workflows per hour
    workflow_results: List[ExecutionResult] = None
    
    def __post_init__(self):
        if self.workflow_results is None:
            self.workflow_results = []

@dataclass
class RecoveryAction:
    """Action to take when handling service failure"""
    action_type: RecoveryStrategy
    alternative_service_id: Optional[int] = None
    retry_count: int = 0
    delay_seconds: int = 0
    message: str = ""

class WorkflowEngine:
    """Advanced workflow execution with dynamic routing and error handling"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.service_registry = ServiceRegistry(db_session)
        self.task_scheduler = TaskScheduler(db_session)
        self.capability_matcher = CapabilityMatcher(db_session)
        
        # Engine configuration
        self.default_execution_mode = ExecutionMode.OPTIMIZED
        self.default_recovery_strategy = RecoveryStrategy.FALLBACK
        self.max_retries = 3
        self.retry_delay_base = 30  # seconds
        self.health_check_interval = 10  # seconds
        
    async def execute_workflow_optimized(self, 
                                       workflow_id: int,
                                       execution_mode: ExecutionMode = None,
                                       recovery_strategy: RecoveryStrategy = None,
                                       user_preferences: Optional[UserPreferences] = None) -> ExecutionResult:
        """Execute workflow with dynamic service routing and error handling"""
        if execution_mode is None:
            execution_mode = self.default_execution_mode
        if recovery_strategy is None:
            recovery_strategy = self.default_recovery_strategy
            
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting optimized execution of workflow {workflow_id} with mode: {execution_mode}")
            
            # Get workflow and tasks
            workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            tasks = self.db.query(Task).filter(
                Task.workflow_id == workflow_id
            ).order_by(Task.order_index).all()
            
            if not tasks:
                raise ValueError(f"No tasks found for workflow {workflow_id}")
            
            # Update workflow status
            workflow.status = "running"
            workflow.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Schedule tasks if not already scheduled
            await self._ensure_tasks_scheduled(workflow, user_preferences)
            
            # Execute based on mode
            if execution_mode == ExecutionMode.SEQUENTIAL:
                result = await self._execute_sequential(workflow, tasks, recovery_strategy)
            elif execution_mode == ExecutionMode.PARALLEL:
                result = await self._execute_parallel(workflow, tasks, recovery_strategy)
            elif execution_mode == ExecutionMode.OPTIMIZED:
                result = await self._execute_optimized(workflow, tasks, recovery_strategy)
            else:
                raise ValueError(f"Unsupported execution mode: {execution_mode}")
            
            # Update final workflow status
            end_time = datetime.utcnow()
            total_duration = end_time - start_time
            
            if result.success:
                workflow.status = "completed"
            else:
                workflow.status = "failed"
            
            workflow.updated_at = end_time
            self.db.commit()
            
            result.total_duration = total_duration
            result.start_time = start_time
            result.end_time = end_time
            
            logger.info(f"Workflow {workflow_id} execution completed: {result.success}, duration: {total_duration}")
            return result
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} execution failed: {str(e)}")
            
            # Update workflow status to failed
            workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if workflow:
                workflow.status = "failed"
                workflow.updated_at = datetime.utcnow()
                self.db.commit()
            
            return ExecutionResult(
                workflow_id=workflow_id,
                success=False,
                completed_tasks=0,
                failed_tasks=len(tasks) if 'tasks' in locals() else 0,
                total_duration=datetime.utcnow() - start_time,
                start_time=start_time,
                end_time=datetime.utcnow(),
                errors=[f"Execution error: {str(e)}"]
            )

    async def batch_execute_workflows(self, 
                                    workflow_ids: List[int],
                                    optimization_strategy: str = "throughput",
                                    max_concurrent: int = 5) -> BatchResult:
        """Execute multiple workflows with resource optimization"""
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting batch execution of {len(workflow_ids)} workflows")
            
            # Validate all workflows exist
            existing_workflows = self.db.query(Workflow).filter(
                Workflow.id.in_(workflow_ids)
            ).all()
            
            if len(existing_workflows) != len(workflow_ids):
                missing = set(workflow_ids) - {w.id for w in existing_workflows}
                raise ValueError(f"Workflows not found: {list(missing)}")
            
            # Optimize execution order
            ordered_workflows = self._optimize_batch_execution_order(
                existing_workflows, optimization_strategy
            )
            
            # Execute workflows with concurrency control
            semaphore = asyncio.Semaphore(max_concurrent)
            tasks = [
                self._execute_workflow_with_semaphore(semaphore, workflow.id)
                for workflow in ordered_workflows
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful = 0
            failed = 0
            workflow_results = []
            
            for workflow, result in zip(ordered_workflows, results):
                if isinstance(result, Exception):
                    logger.error(f"Workflow {workflow.id} failed with exception: {str(result)}")
                    workflow_results.append(ExecutionResult(
                        workflow_id=workflow.id,
                        success=False,
                        completed_tasks=0,
                        failed_tasks=0,
                        total_duration=timedelta(0),
                        start_time=start_time,
                        end_time=datetime.utcnow(),
                        errors=[str(result)]
                    ))
                    failed += 1
                else:
                    workflow_results.append(result)
                    if result.success:
                        successful += 1
                    else:
                        failed += 1
            
            end_time = datetime.utcnow()
            total_duration = end_time - start_time
            throughput = len(workflow_ids) / (total_duration.total_seconds() / 3600) if total_duration.total_seconds() > 0 else 0
            
            batch_result = BatchResult(
                total_workflows=len(workflow_ids),
                successful_workflows=successful,
                failed_workflows=failed,
                total_duration=total_duration,
                throughput=throughput,
                workflow_results=workflow_results
            )
            
            logger.info(f"Batch execution completed: {successful}/{len(workflow_ids)} successful, throughput: {throughput:.2f} workflows/hour")
            return batch_result
            
        except Exception as e:
            logger.error(f"Batch execution failed: {str(e)}")
            raise

    async def handle_service_failure(self, 
                                   failed_task: Task,
                                   failed_service: ServiceV2,
                                   recovery_strategy: RecoveryStrategy = None) -> RecoveryAction:
        """Handle service failures with automatic recovery"""
        if recovery_strategy is None:
            recovery_strategy = self.default_recovery_strategy
            
        try:
            logger.warning(f"Handling service failure for task {failed_task.id}, service {failed_service.id}")
            
            if recovery_strategy == RecoveryStrategy.FAIL_FAST:
                return RecoveryAction(
                    action_type=RecoveryStrategy.FAIL_FAST,
                    message="Failing fast due to service failure"
                )
            
            elif recovery_strategy == RecoveryStrategy.RETRY:
                # Get current retry count
                queue_entry = self.db.query(WorkflowExecutionQueue).filter(
                    WorkflowExecutionQueue.task_id == failed_task.id
                ).first()
                
                if queue_entry and queue_entry.retry_count < self.max_retries:
                    return RecoveryAction(
                        action_type=RecoveryStrategy.RETRY,
                        retry_count=queue_entry.retry_count + 1,
                        delay_seconds=self.retry_delay_base * (2 ** queue_entry.retry_count),
                        message=f"Retrying task (attempt {queue_entry.retry_count + 1})"
                    )
                else:
                    # Max retries exceeded, try fallback
                    recovery_strategy = RecoveryStrategy.FALLBACK
            
            if recovery_strategy == RecoveryStrategy.FALLBACK:
                # Find alternative service
                available_services = await self.service_registry.get_available_services()
                available_services = [s for s in available_services if s.id != failed_service.id]
                
                if available_services:
                    alternative = await self.task_scheduler.resolve_task_service_mapping(
                        failed_task, available_services
                    )
                    
                    if alternative:
                        return RecoveryAction(
                            action_type=RecoveryStrategy.FALLBACK,
                            alternative_service_id=alternative.id,
                            message=f"Switching to alternative service: {alternative.name}"
                        )
            
            # If all else fails, continue with other tasks
            return RecoveryAction(
                action_type=RecoveryStrategy.CONTINUE,
                message="Continuing with remaining tasks"
            )
            
        except Exception as e:
            logger.error(f"Recovery handling failed: {str(e)}")
            return RecoveryAction(
                action_type=RecoveryStrategy.FAIL_FAST,
                message=f"Recovery failed: {str(e)}"
            )

    # Private methods
    
    async def _ensure_tasks_scheduled(self, 
                                    workflow: Workflow,
                                    user_preferences: Optional[UserPreferences] = None):
        """Ensure all workflow tasks are scheduled"""
        # Check if tasks are already scheduled
        scheduled_count = self.db.query(WorkflowExecutionQueue).filter(
            WorkflowExecutionQueue.workflow_id == workflow.id
        ).count()
        
        tasks_count = self.db.query(Task).filter(
            Task.workflow_id == workflow.id
        ).count()
        
        if scheduled_count < tasks_count:
            logger.info(f"Scheduling remaining tasks for workflow {workflow.id}")
            await self.task_scheduler.schedule_workflow(workflow, user_preferences)

    async def _execute_sequential(self, 
                                workflow: Workflow,
                                tasks: List[Task],
                                recovery_strategy: RecoveryStrategy) -> ExecutionResult:
        """Execute tasks sequentially"""
        completed = 0
        failed = 0
        task_results = {}
        errors = []
        
        for task in tasks:
            try:
                result = await self._execute_single_task(task, recovery_strategy)
                if result.get('success', False):
                    completed += 1
                    task_results[task.id] = result
                else:
                    failed += 1
                    errors.append(f"Task {task.id} failed: {result.get('message', 'Unknown error')}")
                    
                    if recovery_strategy == RecoveryStrategy.FAIL_FAST:
                        break
                        
            except Exception as e:
                failed += 1
                errors.append(f"Task {task.id} exception: {str(e)}")
                
                if recovery_strategy == RecoveryStrategy.FAIL_FAST:
                    break
        
        return ExecutionResult(
            workflow_id=workflow.id,
            success=failed == 0,
            completed_tasks=completed,
            failed_tasks=failed,
            total_duration=timedelta(0),  # Will be set by caller
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            task_results=task_results,
            errors=errors
        )

    async def _execute_parallel(self, 
                              workflow: Workflow,
                              tasks: List[Task],
                              recovery_strategy: RecoveryStrategy) -> ExecutionResult:
        """Execute independent tasks in parallel"""
        # Analyze dependencies to find parallelizable tasks
        dependencies = self.task_scheduler._analyze_task_dependencies(workflow.id)
        
        # Group tasks by dependency level
        task_levels = self._group_tasks_by_dependency_level(tasks, dependencies)
        
        completed = 0
        failed = 0
        task_results = {}
        errors = []
        
        # Execute each level in sequence, but tasks within level in parallel
        for level, level_tasks in task_levels.items():
            if not level_tasks:
                continue
                
            # Execute tasks in this level concurrently
            task_coroutines = [
                self._execute_single_task(task, recovery_strategy)
                for task in level_tasks
            ]
            
            results = await asyncio.gather(*task_coroutines, return_exceptions=True)
            
            level_failed = False
            for task, result in zip(level_tasks, results):
                if isinstance(result, Exception):
                    failed += 1
                    errors.append(f"Task {task.id} exception: {str(result)}")
                    level_failed = True
                elif result.get('success', False):
                    completed += 1
                    task_results[task.id] = result
                else:
                    failed += 1
                    errors.append(f"Task {task.id} failed: {result.get('message', 'Unknown error')}")
                    level_failed = True
            
            # Stop if any task in level failed and using fail-fast strategy
            if level_failed and recovery_strategy == RecoveryStrategy.FAIL_FAST:
                break
        
        return ExecutionResult(
            workflow_id=workflow.id,
            success=failed == 0,
            completed_tasks=completed,
            failed_tasks=failed,
            total_duration=timedelta(0),  # Will be set by caller
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            task_results=task_results,
            errors=errors
        )

    async def _execute_optimized(self, 
                               workflow: Workflow,
                               tasks: List[Task],
                               recovery_strategy: RecoveryStrategy) -> ExecutionResult:
        """Execute with optimal resource utilization and dependency management"""
        # For now, use parallel execution as the optimized approach
        # In a full implementation, this would include:
        # - Resource-aware scheduling
        # - Dynamic load balancing
        # - Predictive service selection
        # - Cost optimization
        
        return await self._execute_parallel(workflow, tasks, recovery_strategy)

    async def _execute_single_task(self, 
                                 task: Task,
                                 recovery_strategy: RecoveryStrategy) -> Dict[str, Any]:
        """Execute a single task with error handling"""
        try:
            # Get queue entry for this task
            queue_entry = self.db.query(WorkflowExecutionQueue).filter(
                WorkflowExecutionQueue.task_id == task.id
            ).first()
            
            if not queue_entry:
                return {
                    'success': False,
                    'message': 'Task not found in execution queue'
                }
            
            # Get assigned service
            service = self.db.query(Service).filter(
                Service.id == queue_entry.assigned_service_id
            ).first()
            
            if not service:
                return {
                    'success': False,
                    'message': 'Assigned service not found'
                }
            
            # Update queue entry status
            queue_entry.status = QueueStatus.RUNNING
            queue_entry.actual_start_time = datetime.utcnow()
            queue_entry.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Execute task on service
            result = await self._call_service_for_task(service, task)
            
            # Update queue entry with result
            if result.get('success', False):
                queue_entry.status = QueueStatus.COMPLETED
                task.status = "completed"
                
                # Store result
                task_result = Result(
                    task_id=task.id,
                    data=result.get('data', {}),
                    created_at=datetime.utcnow()
                )
                self.db.add(task_result)
                
                # Update service load
                await self.service_registry.update_service_load(service.id, -1)
                
            else:
                queue_entry.status = QueueStatus.FAILED
                task.status = "failed"
                
                # Handle failure
                recovery_action = await self.handle_service_failure(task, service, recovery_strategy)
                
                if recovery_action.action_type == RecoveryStrategy.FALLBACK and recovery_action.alternative_service_id:
                    # Try with alternative service
                    alt_service = self.db.query(Service).filter(
                        Service.id == recovery_action.alternative_service_id
                    ).first()
                    
                    if alt_service:
                        queue_entry.assigned_service_id = alt_service.id
                        queue_entry.retry_count += 1
                        result = await self._call_service_for_task(alt_service, task)
                        
                        if result.get('success', False):
                            queue_entry.status = QueueStatus.COMPLETED
                            task.status = "completed"
                            await self.service_registry.update_service_load(alt_service.id, -1)
            
            self.db.commit()
            return result
            
        except Exception as e:
            logger.error(f"Task {task.id} execution failed: {str(e)}")
            
            if 'queue_entry' in locals():
                queue_entry.status = QueueStatus.FAILED
                self.db.commit()
            
            return {
                'success': False,
                'message': f'Execution error: {str(e)}'
            }

    async def _call_service_for_task(self, service: Service, task: Task) -> Dict[str, Any]:
        """Call service to execute task"""
        try:
            # This is a simplified implementation
            # In reality, this would make HTTP calls to the service endpoints
            # and handle the specific protocols for each service type
            
            import httpx
            import json
            
            # Prepare task parameters
            params = task.service_parameters or {}
            
            # Add sample_id if not present
            if 'sample_id' not in params:
                params['sample_id'] = f"WF{task.workflow_id}_T{task.id}_{task.name}".replace(" ", "_")
            
            # Determine service endpoint based on service type
            if service.type == "sample_prep":
                endpoint = f"{service.endpoint}/prepare"
            elif service.type == "hplc":
                endpoint = f"{service.endpoint}/analyze"
            else:
                endpoint = f"{service.endpoint}/execute"
            
            # Make service call
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    endpoint,
                    json=params,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200 or response.status_code == 202:
                    # Task started successfully, now monitor completion
                    results = await self._monitor_task_completion(service, task, client)
                    return results
                else:
                    return {
                        'success': False,
                        'message': f'Service call failed with status {response.status_code}: {response.text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'message': f'Service call exception: {str(e)}'
            }

    async def _monitor_task_completion(self, 
                                     service: Service,
                                     task: Task,
                                     client: httpx.AsyncClient) -> Dict[str, Any]:
        """Monitor task completion on service"""
        max_wait_time = getattr(task, 'timeout_seconds', 3600)  # Default 1 hour
        check_interval = 10  # seconds
        elapsed_time = 0
        
        results_endpoint = f"{service.endpoint}/results"
        
        while elapsed_time < max_wait_time:
            try:
                # Check for results
                response = await client.get(results_endpoint)
                
                if response.status_code == 200:
                    result_data = response.json()
                    
                    # Check if task is completed
                    if result_data.get('instrument_status') == 'completed':
                        return {
                            'success': True,
                            'data': result_data,
                            'duration_seconds': elapsed_time
                        }
                    elif result_data.get('instrument_status') == 'failed':
                        return {
                            'success': False,
                            'message': 'Task failed on service',
                            'data': result_data
                        }
                    
                    # Task still running, wait and check again
                    await asyncio.sleep(check_interval)
                    elapsed_time += check_interval
                    
                else:
                    # Error getting results
                    await asyncio.sleep(check_interval)
                    elapsed_time += check_interval
                    
            except Exception as e:
                logger.warning(f"Error checking task results: {str(e)}")
                await asyncio.sleep(check_interval)
                elapsed_time += check_interval
        
        # Timeout reached
        return {
            'success': False,
            'message': f'Task timeout after {max_wait_time} seconds'
        }

    def _group_tasks_by_dependency_level(self, 
                                       tasks: List[Task],
                                       dependencies: Dict[int, List[int]]) -> Dict[int, List[Task]]:
        """Group tasks by dependency level for parallel execution"""
        task_dict = {task.id: task for task in tasks}
        levels = {}
        task_levels = {}
        
        def calculate_level(task_id: int) -> int:
            if task_id in task_levels:
                return task_levels[task_id]
            
            if task_id not in dependencies or not dependencies[task_id]:
                # No dependencies, level 0
                task_levels[task_id] = 0
                return 0
            
            # Level is max of dependency levels + 1
            max_dep_level = max(calculate_level(dep_id) for dep_id in dependencies[task_id])
            task_levels[task_id] = max_dep_level + 1
            return max_dep_level + 1
        
        # Calculate level for each task
        for task in tasks:
            level = calculate_level(task.id)
            if level not in levels:
                levels[level] = []
            levels[level].append(task)
        
        return levels

    def _optimize_batch_execution_order(self, 
                                      workflows: List[Workflow],
                                      strategy: str) -> List[Workflow]:
        """Optimize execution order for batch processing"""
        if strategy == "throughput":
            # Order by estimated duration (shortest first)
            return sorted(workflows, key=lambda w: self._estimate_workflow_duration(w))
        
        elif strategy == "priority":
            # Order by workflow priority (if available in metadata)
            return sorted(workflows, key=lambda w: w.metadata.get('priority', 5) if w.metadata else 5)
        
        elif strategy == "fifo":
            # First in, first out
            return sorted(workflows, key=lambda w: w.created_at)
        
        else:
            # Default to FIFO
            return sorted(workflows, key=lambda w: w.created_at)

    def _estimate_workflow_duration(self, workflow: Workflow) -> int:
        """Estimate workflow duration in seconds"""
        # This is a simplified estimation
        # In practice, you'd sum up task durations considering dependencies
        
        task_count = self.db.query(Task).filter(Task.workflow_id == workflow.id).count()
        return task_count * 3600  # Assume 1 hour per task on average

    async def _execute_workflow_with_semaphore(self, 
                                             semaphore: asyncio.Semaphore,
                                             workflow_id: int) -> ExecutionResult:
        """Execute workflow with concurrency control"""
        async with semaphore:
            return await self.execute_workflow_optimized(workflow_id)