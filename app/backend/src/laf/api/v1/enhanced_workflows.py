"""
Enhanced Workflow Management API - Advanced scheduling and execution control
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from ...core.database import get_db
from ...models.enhanced_models import WorkflowExecutionQueue, QueueStatus
from ...models.database import Workflow
from ...schemas.enhanced_schemas import (
    QueueEntryResponse, QueueStatusResponse, WorkflowScheduleRequest, 
    WorkflowScheduleResponse, ExecutionResultResponse, BatchExecutionRequest, 
    BatchExecutionResponse
)
from ...core.task_scheduler import TaskScheduler, SchedulingStrategy, UserPreferences
from ...core.workflow_engine import WorkflowEngine, ExecutionMode, RecoveryStrategy

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/workflows", tags=["Enhanced Workflows"])

@router.post("/{workflow_id}/schedule", response_model=WorkflowScheduleResponse)
async def schedule_workflow(
    workflow_id: int,
    schedule_request: WorkflowScheduleRequest,
    db: Session = Depends(get_db)
):
    """
    Schedule a workflow for execution with advanced options
    
    **Scheduling Process:**
    1. Analyzes workflow tasks and dependencies
    2. Matches tasks to available services
    3. Creates optimized execution queue
    4. Provides time estimates and service assignments
    """
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Build scheduling strategy
        try:
            strategy = SchedulingStrategy(schedule_request.strategy)
        except ValueError:
            strategy = SchedulingStrategy.PRIORITY
        
        # Build user preferences if provided
        user_preferences = None
        if schedule_request.user_preferences:
            prefs = schedule_request.user_preferences
            user_preferences = UserPreferences(
                user_id=prefs.get('user_id', 'system'),
                priority_weight=prefs.get('priority_weight', 0.5),
                cost_weight=prefs.get('cost_weight', 0.3),
                speed_weight=prefs.get('speed_weight', 0.7),
                reliability_weight=prefs.get('reliability_weight', 0.8),
                preferred_services=prefs.get('preferred_services', []),
                blacklisted_services=prefs.get('blacklisted_services', [])
            )
        
        # Schedule workflow
        scheduler = TaskScheduler(db)
        schedule_result = await scheduler.schedule_workflow(
            workflow, user_preferences, strategy
        )
        
        response = WorkflowScheduleResponse(
            workflow_id=workflow_id,
            success=schedule_result.success,
            scheduled_tasks=schedule_result.scheduled_tasks,
            failed_tasks=schedule_result.failed_tasks,
            estimated_start_time=schedule_result.estimated_start_time,
            estimated_completion_time=schedule_result.estimated_completion_time,
            assigned_services=schedule_result.assigned_services,
            queue_positions=schedule_result.queue_positions,
            errors=schedule_result.errors,
            warnings=schedule_result.warnings
        )
        
        logger.info(f"Scheduled workflow {workflow_id}: {schedule_result.scheduled_tasks} tasks")
        return response
        
    except Exception as e:
        logger.error(f"Failed to schedule workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow scheduling failed: {str(e)}")

@router.post("/{workflow_id}/execute", response_model=ExecutionResultResponse)
async def execute_workflow(
    workflow_id: int,
    execution_mode: Optional[str] = "optimized",
    recovery_strategy: Optional[str] = "fallback",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Execute a workflow with advanced execution control
    
    **Execution Modes:**
    - **sequential**: Execute tasks one by one
    - **parallel**: Execute independent tasks concurrently
    - **optimized**: Smart execution with resource awareness
    
    **Recovery Strategies:**
    - **fail_fast**: Stop on first failure
    - **continue**: Skip failed tasks and continue
    - **retry**: Retry failed tasks
    - **fallback**: Use alternative services
    """
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Parse execution parameters
        try:
            exec_mode = ExecutionMode(execution_mode)
        except ValueError:
            exec_mode = ExecutionMode.OPTIMIZED
            
        try:
            recovery_strat = RecoveryStrategy(recovery_strategy)
        except ValueError:
            recovery_strat = RecoveryStrategy.FALLBACK
        
        # Execute workflow
        engine = WorkflowEngine(db)
        result = await engine.execute_workflow_optimized(
            workflow_id, exec_mode, recovery_strat
        )
        
        response = ExecutionResultResponse(
            workflow_id=result.workflow_id,
            success=result.success,
            completed_tasks=result.completed_tasks,
            failed_tasks=result.failed_tasks,
            total_duration_seconds=result.total_duration.total_seconds(),
            start_time=result.start_time,
            end_time=result.end_time,
            task_results=result.task_results,
            errors=result.errors,
            warnings=result.warnings
        )
        
        logger.info(f"Executed workflow {workflow_id}: success={result.success}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to execute workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@router.post("/batch-execute", response_model=BatchExecutionResponse)
async def batch_execute_workflows(
    batch_request: BatchExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Execute multiple workflows in batch with optimization
    
    **Optimization Strategies:**
    - **throughput**: Maximize workflows per hour
    - **priority**: Execute by workflow priority
    - **fifo**: First in, first out
    """
    try:
        # Validate workflows exist
        workflows = db.query(Workflow).filter(Workflow.id.in_(batch_request.workflow_ids)).all()
        if len(workflows) != len(batch_request.workflow_ids):
            found_ids = {w.id for w in workflows}
            missing_ids = set(batch_request.workflow_ids) - found_ids
            raise HTTPException(status_code=404, detail=f"Workflows not found: {list(missing_ids)}")
        
        # Execute batch
        engine = WorkflowEngine(db)
        batch_result = await engine.batch_execute_workflows(
            batch_request.workflow_ids,
            batch_request.optimization_strategy,
            batch_request.max_concurrent
        )
        
        # Convert results
        workflow_results = [
            ExecutionResultResponse(
                workflow_id=result.workflow_id,
                success=result.success,
                completed_tasks=result.completed_tasks,
                failed_tasks=result.failed_tasks,
                total_duration_seconds=result.total_duration.total_seconds(),
                start_time=result.start_time,
                end_time=result.end_time,
                task_results=result.task_results,
                errors=result.errors,
                warnings=result.warnings
            )
            for result in batch_result.workflow_results
        ]
        
        response = BatchExecutionResponse(
            total_workflows=batch_result.total_workflows,
            successful_workflows=batch_result.successful_workflows,
            failed_workflows=batch_result.failed_workflows,
            total_duration_seconds=batch_result.total_duration.total_seconds(),
            throughput_workflows_per_hour=batch_result.throughput,
            workflow_results=workflow_results
        )
        
        logger.info(f"Batch executed {len(batch_request.workflow_ids)} workflows: {batch_result.successful_workflows} successful")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch execution failed: {str(e)}")

@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status(db: Session = Depends(get_db)):
    """Get current execution queue status and metrics"""
    try:
        scheduler = TaskScheduler(db)
        queue_status = await scheduler.get_queue_status()
        
        return QueueStatusResponse(
            total_entries=queue_status["total_entries"],
            status_breakdown=queue_status["status_breakdown"],
            average_wait_times=queue_status["average_wait_times"],
            service_utilization=queue_status["service_utilization"],
            timestamp=queue_status["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get queue status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Queue status retrieval failed: {str(e)}")

@router.get("/queue/entries", response_model=List[QueueEntryResponse])
async def list_queue_entries(
    status: Optional[str] = None,
    workflow_id: Optional[int] = None,
    service_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List execution queue entries with optional filtering"""
    try:
        query = db.query(WorkflowExecutionQueue)
        
        if status:
            try:
                queue_status = QueueStatus(status)
                query = query.filter(WorkflowExecutionQueue.status == queue_status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        if workflow_id:
            query = query.filter(WorkflowExecutionQueue.workflow_id == workflow_id)
        
        if service_id:
            query = query.filter(WorkflowExecutionQueue.assigned_service_id == service_id)
        
        entries = query.order_by(WorkflowExecutionQueue.created_at.desc()).limit(limit).all()
        
        return entries
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list queue entries: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Queue entries retrieval failed: {str(e)}")

@router.post("/queue/rebalance")
async def rebalance_queue(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger queue rebalancing for optimization"""
    try:
        scheduler = TaskScheduler(db)
        
        # Run rebalancing in background
        background_tasks.add_task(scheduler.rebalance_queue)
        
        pending_count = db.query(WorkflowExecutionQueue).filter(
            WorkflowExecutionQueue.status == QueueStatus.PENDING
        ).count()
        
        return {
            "message": "Queue rebalancing initiated",
            "pending_entries": pending_count,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to initiate queue rebalancing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Queue rebalancing failed: {str(e)}")

@router.get("/{workflow_id}/execution-estimate")
async def get_workflow_execution_estimate(workflow_id: int, db: Session = Depends(get_db)):
    """Get execution time and resource estimates for a workflow"""
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        scheduler = TaskScheduler(db)
        estimate = await scheduler.estimate_execution_time(workflow)
        
        return {
            "workflow_id": workflow_id,
            "total_estimated_duration_seconds": estimate.total_estimated_duration.total_seconds(),
            "critical_path_duration_seconds": estimate.critical_path_duration.total_seconds(),
            "earliest_start_time": estimate.earliest_start_time,
            "estimated_completion_time": estimate.estimated_completion_time,
            "resource_requirements": estimate.resource_requirements,
            "bottlenecks": estimate.bottlenecks,
            "parallelizable_tasks": estimate.parallelizable_tasks,
            "cost_estimate": estimate.cost_estimate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to estimate workflow execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Execution estimation failed: {str(e)}")

@router.post("/{workflow_id}/priority")
async def update_workflow_priority(
    workflow_id: int,
    priority: int,
    db: Session = Depends(get_db)
):
    """Update priority for all tasks in a workflow queue"""
    try:
        if not (1 <= priority <= 10):
            raise HTTPException(status_code=400, detail="Priority must be between 1 and 10")
        
        # Update all queue entries for this workflow
        updated_count = db.query(WorkflowExecutionQueue).filter(
            WorkflowExecutionQueue.workflow_id == workflow_id,
            WorkflowExecutionQueue.status == QueueStatus.PENDING
        ).update({"priority": priority, "updated_at": datetime.utcnow()})
        
        db.commit()
        
        return {
            "workflow_id": workflow_id,
            "new_priority": priority,
            "updated_tasks": updated_count,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update workflow priority: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Priority update failed: {str(e)}")

@router.delete("/{workflow_id}/cancel")
async def cancel_workflow_execution(workflow_id: int, db: Session = Depends(get_db)):
    """Cancel pending workflow execution"""
    try:
        # Cancel all pending tasks for this workflow
        cancelled_count = db.query(WorkflowExecutionQueue).filter(
            WorkflowExecutionQueue.workflow_id == workflow_id,
            WorkflowExecutionQueue.status == QueueStatus.PENDING
        ).update({
            "status": QueueStatus.CANCELLED,
            "updated_at": datetime.utcnow()
        })
        
        # Update workflow status
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if workflow:
            workflow.status = "cancelled"
            workflow.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "workflow_id": workflow_id,
            "cancelled_tasks": cancelled_count,
            "message": "Workflow execution cancelled",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to cancel workflow execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow cancellation failed: {str(e)}")