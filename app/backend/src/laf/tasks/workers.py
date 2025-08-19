import logging
import time
import json
import requests
from typing import Dict, Any, Optional

from .celery_app import celery_app
from ..core.database import SessionLocal
from ..models.database import Task, Service, Workflow

# Conditional imports for different deployment targets
try:
    from ..services.clients.k8s_client import KubernetesClient
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False
    KubernetesClient = None

try:
    from ..services.clients.docker_client import DockerClient
    DOCKER_CLIENT_AVAILABLE = True
except ImportError:
    DOCKER_CLIENT_AVAILABLE = False
    DockerClient = None

logger = logging.getLogger(__name__)

# Task name to service mapping for HTTP-based lab instruments
LAB_INSTRUMENT_MAPPING = {
    "Sample Preparation": {
        "endpoint": "http://sample-prep-station:5002",
        "action": "prepare"
    },
    "Sample Preparation Station": {
        "endpoint": "http://sample-prep-station:5002",
        "action": "prepare"
    },
    "HPLC Analysis System": {
        "endpoint": "http://hplc-system:5003", 
        "action": "analyze"
    },
    "HPLC Purity Analysis": {
        "endpoint": "http://hplc-system:5003",
        "action": "analyze"
    },
    "HPLC Analysis": {
        "endpoint": "http://hplc-system:5003",
        "action": "analyze"
    }
}


@celery_app.task
def launch_service(
    task_id: int, service_id: int, parameters: Optional[Dict[str, Any]] = None
):
    """Launch a service for a task"""
    db = SessionLocal()
    task = None

    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        service = db.query(Service).filter(Service.id == service_id).first()

        if not task or not service:
            logger.error(
                f"Task or service not found (task_id={task_id}, service_id={service_id})"
            )
            return

        # Merge default parameters with task-specific parameters
        merged_params: Dict[str, str] = {}
        if service.default_parameters is not None:
            merged_params.update(dict(service.default_parameters))  # type: ignore
        if parameters:
            merged_params.update(parameters)

        # Launch based on service type
        service_type = str(service.type)
        service_endpoint = str(service.endpoint)

        if service_type == "kubernetes":
            if K8S_AVAILABLE and KubernetesClient:
                k8s_client = KubernetesClient()
                job_name = f"task-{task_id}-{service.name.lower()}"
                k8s_client.launch_job(
                    job_name=job_name,
                    image=service_endpoint,
                    env=merged_params,
                    namespace="default",
                )
                logger.info(f"Launched Kubernetes job {job_name} for task {task_id}")
            else:
                logger.error("Kubernetes client not available")
                task.status = "failed"
                db.commit()
                return

        elif service_type == "docker":
            if DOCKER_CLIENT_AVAILABLE and DockerClient:
                docker_client = DockerClient()
                container_id = docker_client.launch_container(
                    image=service_endpoint, env=merged_params
                )
                logger.info(f"Launched Docker container {container_id} for task {task_id}")
            else:
                logger.error("Docker client not available")
                task.status = "failed"
                db.commit()
                return

        elif service_type == "http":
            import requests

            response = requests.post(service_endpoint, json=merged_params, timeout=30)
            response.raise_for_status()
            logger.info(f"Called HTTP endpoint {service_endpoint} for task {task_id}")

        else:
            logger.error(f"Unknown service type: {service_type}")
            task.status = "failed"  # type: ignore
            db.commit()
            return

        # Update task status to running
        task.status = "running"  # type: ignore
        db.commit()

    except Exception as e:
        logger.error(f"Error launching service: {e}")
        if task:
            task.status = "failed"  # type: ignore
            db.commit()
    finally:
        db.close()


@celery_app.task(bind=True)
def execute_workflow(self, workflow_id: int):
    """Execute an entire workflow using Celery for concurrency and scalability"""
    db = SessionLocal()
    
    try:
        # Get workflow and tasks
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return {"status": "error", "message": "Workflow not found"}
        
        logger.info(f"Starting workflow execution: {workflow.name} (ID: {workflow_id})")
        
        # Update workflow status
        workflow.status = "running"
        db.commit()
        
        # Get tasks in order
        tasks = sorted(workflow.tasks, key=lambda x: x.order_index)
        
        # Execute tasks sequentially using Celery chain with callback
        from celery import chain
        
        # Build a chain of task executions using immutable signatures
        task_chain = []
        for task in tasks:
            if task.service_id:
                logger.info(f"Queuing task: {task.name} (ID: {task.id})")
                # Use immutable signature to prevent result passing between tasks
                task_chain.append(execute_lab_task.si(task.id))
        
        if task_chain:
            # Execute tasks as a chain (sequential execution) with callback
            workflow_chain = chain(*task_chain)
            # Add callback to mark workflow complete when chain finishes
            workflow_chain.apply_async(link=complete_workflow.si(workflow_id))
            # Schedule periodic checks to ensure completion is detected
            complete_workflow.apply_async(args=[workflow_id], countdown=30)  # Check after 30 seconds
            complete_workflow.apply_async(args=[workflow_id], countdown=60)  # Check after 1 minute
            complete_workflow.apply_async(args=[workflow_id], countdown=120)  # Check after 2 minutes
            logger.info(f"Workflow {workflow_id} task chain started with {len(task_chain)} tasks")
            
            # Keep workflow in running state while tasks execute
            return {"status": "running", "workflow_id": workflow_id, "tasks_queued": len(task_chain)}
        else:
            # No tasks to execute
            workflow.status = "completed"
            db.commit()
            logger.info(f"Workflow {workflow_id} completed (no executable tasks)")
            return {"status": "completed", "workflow_id": workflow_id}
        
    except Exception as e:
        logger.error(f"Workflow {workflow_id} execution error: {str(e)}")
        if workflow:
            workflow.status = "failed"
            db.commit()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True)
def execute_lab_task(self, task_id: int):
    """Execute a single lab task using HTTP communication"""
    db = SessionLocal()
    
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return {"status": "error", "message": "Task not found"}
        
        logger.info(f"Executing lab task: {task.name} (ID: {task_id})")
        
        # Update task status
        task.status = "running"
        db.commit()
        
        # Get instrument mapping
        if task.name not in LAB_INSTRUMENT_MAPPING:
            logger.error(f"No instrument mapping for task: {task.name}")
            task.status = "failed"
            db.commit()
            return {"status": "error", "message": f"No mapping for {task.name}"}
        
        mapping = LAB_INSTRUMENT_MAPPING[task.name]
        endpoint = mapping["endpoint"]
        action = mapping["action"]
        
        # Get task parameters
        params = task.service_parameters
        if isinstance(params, str):
            params = json.loads(params)
        
        # Reset instrument
        requests.post(f"{endpoint}/reset", timeout=10)
        time.sleep(1)
        
        # Start task execution
        response = requests.post(f"{endpoint}/{action}", json=params, timeout=30)
        if response.status_code != 202:
            error_msg = f"Failed to start {task.name}: HTTP {response.status_code}"
            logger.error(error_msg)
            task.status = "failed"
            db.commit()
            return {"status": "error", "message": error_msg}
        
        logger.info(f"Task {task_id} started on instrument, monitoring...")
        
        # Monitor execution with timeout
        start_time = time.time()
        while time.time() - start_time < 300:  # 5 minute timeout
            try:
                status_response = requests.get(f"{endpoint}/status", timeout=10)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    instrument_status = status_data.get('status')
                    
                    if instrument_status == 'completed':
                        # Get results
                        results_response = requests.get(f"{endpoint}/results", timeout=10)
                        if results_response.status_code == 200:
                            results = results_response.json()
                            
                            # Save results to database
                            from ..models.database import Result
                            result_record = Result(
                                task_id=task.id,
                                data=results
                            )
                            db.add(result_record)
                            
                            # Update task
                            task.status = "completed"
                            db.commit()
                            
                            logger.info(f"Task {task_id} completed successfully")
                            return {"status": "completed", "task_id": task_id, "results": results}
                    
                    elif instrument_status in ['failed', 'aborted']:
                        error_msg = f"Instrument reported {instrument_status}"
                        logger.error(f"Task {task_id}: {error_msg}")
                        task.status = "failed"
                        db.commit()
                        return {"status": "failed", "message": error_msg}
                
                time.sleep(3)
            except requests.exceptions.RequestException as e:
                logger.warning(f"Monitoring error for task {task_id}: {str(e)}")
                time.sleep(5)
        
        # Timeout
        error_msg = "Task execution timeout"
        logger.error(f"Task {task_id}: {error_msg}")
        task.status = "failed" 
        db.commit()
        return {"status": "failed", "message": error_msg}
        
    except Exception as e:
        logger.error(f"Lab task {task_id} execution error: {str(e)}")
        if task:
            task.status = "failed"
            db.commit()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task
def complete_workflow(workflow_id: int):
    """Mark workflow as completed after all tasks finish"""
    db = SessionLocal()
    
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if workflow:
            # Check task completion FIRST
            tasks = workflow.tasks
            completed_tasks = [t for t in tasks if t.status == 'completed']
            failed_tasks = [t for t in tasks if t.status == 'failed']
            running_tasks = [t for t in tasks if t.status == 'running']
            pending_tasks = [t for t in tasks if t.status == 'pending']
            
            logger.info(f"Workflow {workflow_id} task status: {len(completed_tasks)} completed, {len(failed_tasks)} failed, {len(running_tasks)} running, {len(pending_tasks)} pending")
            
            # Only mark workflow complete if ALL tasks are done (completed or failed)
            if len(completed_tasks) + len(failed_tasks) == len(tasks):
                if len(failed_tasks) > 0:
                    workflow.status = "failed"
                    logger.info(f"Workflow {workflow_id} marked as failed due to {len(failed_tasks)} failed tasks")
                else:
                    workflow.status = "completed"
                    logger.info(f"Workflow {workflow_id} marked as completed - all {len(completed_tasks)} tasks completed successfully")
                
                db.commit()
            else:
                logger.info(f"Workflow {workflow_id} still has running/pending tasks - keeping status as running")
                # Don't change status yet - workflow is still in progress
        else:
            logger.error(f"Workflow {workflow_id} not found for completion")
    except Exception as e:
        logger.error(f"Error completing workflow {workflow_id}: {str(e)}")
    finally:
        db.close()
    
    return {"status": "checked", "workflow_id": workflow_id}


@celery_app.task
def execute_concurrent_workflows(workflow_ids: list):
    """Execute multiple workflows concurrently - useful for parallel experiments"""
    logger.info(f"Starting concurrent execution of {len(workflow_ids)} workflows")
    
    # Launch all workflows asynchronously
    job_group = celery_app.group(execute_workflow.s(wf_id) for wf_id in workflow_ids)
    result = job_group.apply_async()
    
    # Return job group ID for tracking
    return {"status": "started", "job_group_id": str(result.id), "workflow_count": len(workflow_ids)}
