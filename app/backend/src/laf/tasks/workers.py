import logging
import time
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timezone

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

# Enhanced task mapping with task types and endpoints for powder_01 workflow
LAB_INSTRUMENT_MAPPING = {
    # Manual Tasks - require user interaction
    "Sample Measurement": {
        "type": "manual",
        "requires_user_input": True,
        "description": "Manual data entry by scientist",
        "default_status": "awaiting_manual_completion"
    },
    
    # Service Tasks - HTTP endpoints for processing
    "Run Weight Balance": {
        "type": "service", 
        "endpoint": "http://host.docker.internal:6001",  # Service port accessible from Docker
        "action": "process_materials",
        "monitor_completion": True,
        "timeout": 120
    },
    
    # Instrument Tasks - Physical/simulated instruments
    "Weight Balance": {
        "type": "instrument",
        "endpoint": "http://host.docker.internal:5011",  # Weight balance simulator accessible from Docker
        "action": "dispense",
        "monitor_completion": True,
        "timeout": 300
    },
    
    # Legacy mappings for existing workflows
    "Sample Preparation": {
        "type": "instrument",
        "endpoint": "http://sample-prep-station:5002",
        "action": "prepare",
        "monitor_completion": True,
        "timeout": 180
    },
    "Sample Preparation Station": {
        "type": "instrument", 
        "endpoint": "http://sample-prep-station:5002",
        "action": "prepare",
        "monitor_completion": True,
        "timeout": 180
    },
    "HPLC Analysis System": {
        "type": "instrument",
        "endpoint": "http://hplc-system:5003", 
        "action": "analyze",
        "monitor_completion": True,
        "timeout": 300
    },
    "HPLC Purity Analysis": {
        "type": "instrument",
        "endpoint": "http://hplc-system:5003",
        "action": "analyze",
        "monitor_completion": True,
        "timeout": 300
    },
    "HPLC Analysis": {
        "type": "instrument",
        "endpoint": "http://hplc-system:5003",
        "action": "analyze",
        "monitor_completion": True,
        "timeout": 300
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
        
        # Only execute the first task - subsequent tasks will be triggered after completion
        if tasks:
            first_task = tasks[0]
            
            # Queue first task if it has service_id OR if it's mapped in LAB_INSTRUMENT_MAPPING
            if first_task.service_id or first_task.name in LAB_INSTRUMENT_MAPPING:
                logger.info(f"Starting first task: {first_task.name} (ID: {first_task.id})")
                # Execute the first task
                execute_lab_task.delay(first_task.id)
                
                # Schedule periodic checks to ensure completion is detected
                complete_workflow.apply_async(args=[workflow_id], countdown=30)  # Check after 30 seconds
                complete_workflow.apply_async(args=[workflow_id], countdown=60)  # Check after 1 minute
                complete_workflow.apply_async(args=[workflow_id], countdown=120)  # Check after 2 minutes
                complete_workflow.apply_async(args=[workflow_id], countdown=300)  # Check after 5 minutes
                
                logger.info(f"Workflow {workflow_id} started with first task: {first_task.name}")
                
                # Keep workflow in running state while tasks execute
                return {"status": "running", "workflow_id": workflow_id, "first_task": first_task.name}
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


def determine_task_type(task):
    """Determine task type from mapping or task configuration"""
    if task.task_type and task.task_type != "automatic":
        return task.task_type
    
    if task.name in LAB_INSTRUMENT_MAPPING:
        return LAB_INSTRUMENT_MAPPING[task.name].get("type", "instrument")
    
    return "instrument"  # Default to instrument type


@celery_app.task(bind=True)
def execute_lab_task(self, task_id: int):
    """Enhanced task execution with type-specific handling for powder_01 workflow"""
    db = SessionLocal()
    
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return {"status": "error", "message": "Task not found"}
        
        logger.info(f"Executing lab task: {task.name} (ID: {task_id})")
        
        # Determine task type
        task_type = determine_task_type(task)
        logger.info(f"Task {task_id} type: {task_type}")
        
        # Update task type in database
        task.task_type = task_type
        
        result = None
        if task_type == "manual":
            # Manual tasks: Set to awaiting manual completion and return
            task.status = "awaiting_manual_completion"
            task.completion_method = "manual"
            db.commit()
            
            logger.info(f"Task {task_id} set to awaiting manual completion")
            result = {
                "status": "awaiting_manual", 
                "task_id": task_id, 
                "message": "Task awaiting manual completion by scientist"
            }
            
        elif task_type == "service":
            # Service tasks: Execute via HTTP and monitor completion
            result = execute_service_task(task, db)
            
        elif task_type == "instrument":
            # Instrument tasks: Execute via simulator and monitor
            result = execute_instrument_task(task, db)
            
        else:
            # Fallback to legacy execution
            result = execute_legacy_task(task, db)
        
        # If task completed successfully, trigger the next task
        if result and result.get("status") == "completed":
            # Get all tasks in the workflow ordered by order_index
            all_tasks = db.query(Task).filter(Task.workflow_id == task.workflow_id).order_by(Task.order_index).all()
            
            # Find the current task's position
            current_index = next((i for i, t in enumerate(all_tasks) if t.id == task_id), None)
            
            # If there's a next task and it's pending, trigger it
            if current_index is not None and current_index < len(all_tasks) - 1:
                next_task = all_tasks[current_index + 1]
                
                # Only trigger if the next task is pending
                if next_task.status == "pending":
                    logger.info(f"Triggering next task in sequence: {next_task.name} (ID: {next_task.id})")
                    # Queue the next task for execution
                    execute_lab_task.delay(next_task.id)
        
        return result
            
    except Exception as e:
        logger.error(f"Enhanced task {task_id} execution error: {str(e)}")
        if task:
            task.status = "failed"
            db.commit()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


def extract_materials_from_previous_tasks(task, db, params):
    """Extract materials_table from previous completed tasks for Run Weight Balance service"""
    try:
        # Get all tasks in the workflow ordered by order_index
        all_tasks = db.query(Task).filter(Task.workflow_id == task.workflow_id).order_by(Task.order_index).all()
        
        # Find previous completed tasks
        previous_tasks = [t for t in all_tasks if t.order_index < task.order_index and t.status == "completed"]
        
        # Look for Sample Measurement task
        sample_measurement_task = None
        for prev_task in previous_tasks:
            if "Sample Measurement" in prev_task.name:
                sample_measurement_task = prev_task
                break
        
        # If Sample Measurement task found, try to extract materials table
        if sample_measurement_task and sample_measurement_task.service_parameters:
            sample_params = sample_measurement_task.service_parameters
            if isinstance(sample_params, str):
                sample_params = json.loads(sample_params) if sample_params else {}
            
            # Check if there's a materials_table in the sample measurement
            if 'materials_table' in sample_params:
                params['materials_table'] = sample_params['materials_table']
                logger.info(f"Extracted materials_table from {sample_measurement_task.name}: {sample_params['materials_table']}")
            elif 'materials_table' not in params:
                # Create a default materials table based on measurement parameters
                default_table = [{"run": 1, "material_1": 0.1, "material_2": 0.05}]
                params['materials_table'] = default_table
                logger.info(f"Created default materials_table: {default_table}")
        
        elif 'materials_table' not in params:
            # Create a default materials table if none exists
            default_table = [{"run": 1, "material_1": 0.1, "material_2": 0.05}]
            params['materials_table'] = default_table
            logger.info(f"No previous Sample Measurement found, using default materials_table: {default_table}")
        
    except Exception as e:
        logger.error(f"Error extracting materials from previous tasks: {str(e)}")
        # Ensure materials_table exists even if extraction fails
        if 'materials_table' not in params:
            params['materials_table'] = [{"run": 1, "material_1": 0.1, "material_2": 0.05}]
    
    return params


def execute_service_task(task, db):
    """Execute service tasks (like Run Weight Balance)"""
    task_id = task.id
    logger.info(f"Executing service task: {task.name} (ID: {task_id})")
    
    # Update task status
    task.status = "running"
    db.commit()
    
    # Get service mapping
    if task.name not in LAB_INSTRUMENT_MAPPING:
        logger.error(f"No service mapping for task: {task.name}")
        task.status = "failed"
        db.commit()
        return {"status": "error", "message": f"No mapping for {task.name}"}
    
    mapping = LAB_INSTRUMENT_MAPPING[task.name]
    endpoint = mapping["endpoint"]
    action = mapping["action"]
    timeout = mapping.get("timeout", 120)
    
    # Get task parameters
    params = task.service_parameters
    if isinstance(params, str):
        params = json.loads(params) if params else {}
    
    # For Run Weight Balance service, extract materials_table from previous tasks
    if task.name == "Run Weight Balance":
        params = extract_materials_from_previous_tasks(task, db, params)
    
    try:
        # Execute service request
        logger.info(f"Calling service endpoint: {endpoint}/{action}")
        response = requests.post(f"{endpoint}/{action}", json=params, timeout=30)
        
        if response.status_code == 200:
            # Service completed successfully
            results = response.json()
            
            # Save results to database
            from ..models.database import Result
            result_record = Result(
                task_id=task.id,
                data=results
            )
            db.add(result_record)
            
            # Update task
            task.status = "completed"
            task.completion_method = "automatic"
            task.completion_timestamp = datetime.now(timezone.utc)
            db.commit()
            
            logger.info(f"Service task {task_id} completed successfully")
            return {"status": "completed", "task_id": task_id, "results": results}
        
        else:
            error_msg = f"Service failed: HTTP {response.status_code}"
            logger.error(f"Task {task_id}: {error_msg}")
            task.status = "failed"
            db.commit()
            return {"status": "failed", "message": error_msg}
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Service request failed: {str(e)}"
        logger.error(f"Task {task_id}: {error_msg}")
        task.status = "failed"
        db.commit()
        return {"status": "failed", "message": error_msg}


def execute_instrument_task(task, db):
    """Execute instrument tasks (like Weight Balance simulator)"""
    task_id = task.id
    logger.info(f"Executing instrument task: {task.name} (ID: {task_id})")
    
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
    timeout = mapping.get("timeout", 300)
    
    # Get task parameters
    params = task.service_parameters
    if isinstance(params, str):
        params = json.loads(params) if params else {}
    
    # For Weight Balance instrument, extract materials_table from previous task results
    if task.name == "Weight Balance":
        # Get all tasks in the workflow ordered by order_index
        all_tasks = db.query(Task).filter(Task.workflow_id == task.workflow_id).order_by(Task.order_index).all()
        
        # Find previous completed tasks
        previous_tasks = [t for t in all_tasks if t.order_index < task.order_index and t.status == "completed"]
        
        # Look for Run Weight Balance service results
        run_weight_balance_task = None
        for prev_task in previous_tasks:
            if "Run Weight Balance" in prev_task.name:
                run_weight_balance_task = prev_task
                break
        
        if run_weight_balance_task:
            # Get results from the Run Weight Balance service
            from ..models.database import Result
            result_record = db.query(Result).filter(Result.task_id == run_weight_balance_task.id).first()
            
            if result_record and result_record.data:
                service_results = result_record.data
                if isinstance(service_results, str):
                    service_results = json.loads(service_results)
                
                # Extract materials_table from service results if available
                if 'results' in service_results and service_results['results']:
                    # Convert service results to materials table format
                    materials_table = []
                    for result_item in service_results['results']:
                        if 'run' in result_item and 'materials' in result_item:
                            row = {"run": result_item['run']}
                            for material in result_item['materials']:
                                material_name = material.get('material', 'material_1')
                                row[material_name] = material.get('target_weight', 0.1)
                            materials_table.append(row)
                    
                    if materials_table:
                        params['materials_table'] = materials_table
                        logger.info(f"Extracted materials_table for Weight Balance: {materials_table}")
                    else:
                        logger.warning("Could not extract materials_table from Run Weight Balance results")
                        # Use default materials table
                        params['materials_table'] = [{"run": 1, "material_1": 0.1, "material_2": 0.05}]
                else:
                    logger.warning("No valid results found in Run Weight Balance service")
                    # Use default materials table
                    params['materials_table'] = [{"run": 1, "material_1": 0.1, "material_2": 0.05}]
            else:
                logger.warning("No result record found for Run Weight Balance service")
                # Use default materials table
                params['materials_table'] = [{"run": 1, "material_1": 0.1, "material_2": 0.05}]
        else:
            logger.warning("No Run Weight Balance task found in previous tasks")
            # Use default materials table
            params['materials_table'] = [{"run": 1, "material_1": 0.1, "material_2": 0.05}]
        
        # Ensure materials_table exists
        if 'materials_table' not in params:
            params['materials_table'] = [{"run": 1, "material_1": 0.1, "material_2": 0.05}]
            logger.info("Using default materials_table for Weight Balance")
    
    try:
        # Reset instrument
        try:
            requests.post(f"{endpoint}/reset", timeout=10)
            time.sleep(1)
        except:
            logger.warning(f"Could not reset instrument at {endpoint}")
        
        # Start task execution
        logger.info(f"Starting instrument task: {endpoint}/{action}")
        response = requests.post(f"{endpoint}/{action}", json=params, timeout=30)
        
        if response.status_code not in [200, 202]:
            error_msg = f"Failed to start {task.name}: HTTP {response.status_code}"
            logger.error(error_msg)
            task.status = "failed"
            db.commit()
            return {"status": "error", "message": error_msg}
        
        # Check if response contains immediate results (synchronous execution)
        if response.status_code == 200:
            results = response.json()
            if results.get("success"):
                # Save results to database
                from ..models.database import Result
                result_record = Result(
                    task_id=task.id,
                    data=results
                )
                db.add(result_record)
                
                # Update task
                task.status = "completed"
                task.completion_method = "automatic"
                task.completion_timestamp = datetime.now(timezone.utc)
                db.commit()
                
                logger.info(f"Instrument task {task_id} completed successfully")
                return {"status": "completed", "task_id": task_id, "results": results}
        
        # Monitor asynchronous execution
        logger.info(f"Task {task_id} started on instrument, monitoring...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                status_response = requests.get(f"{endpoint}/status", timeout=10)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    instrument_status = status_data.get('status')
                    
                    if instrument_status in ['completed', 'ready']:
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
                            task.completion_method = "automatic"
                            task.completion_timestamp = datetime.now(timezone.utc)
                            db.commit()
                            
                            logger.info(f"Instrument task {task_id} completed successfully")
                            return {"status": "completed", "task_id": task_id, "results": results}
                    
                    elif instrument_status in ['failed', 'aborted', 'error']:
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
        error_msg = f"Instrument execution error: {str(e)}"
        logger.error(f"Task {task_id}: {error_msg}")
        task.status = "failed"
        db.commit()
        return {"status": "error", "error": error_msg}


def execute_legacy_task(task, db):
    """Execute legacy tasks using the original logic"""
    # This is the original execute_lab_task logic for backward compatibility
    task_id = task.id
    
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
