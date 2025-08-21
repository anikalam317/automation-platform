"""
Plugin-based workers for the Laboratory Automation Framework.

This module provides scalable task execution using a plugin architecture
where each task, service, and instrument has its own dedicated plugin.
"""

import logging
import time
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from .celery_app import celery_app
from ..core.database import SessionLocal
from ..models.database import Task, Service, Workflow, Result
from ..plugins.registry import get_plugin_registry
from ..plugins.base import PluginType, TaskPlugin, ServicePlugin, InstrumentPlugin

logger = logging.getLogger(__name__)


def initialize_plugin_system():
    """Initialize the plugin system by discovering and registering plugins."""
    registry = get_plugin_registry()
    
    # Manually register plugins for demonstration (bypassing discovery issues)
    try:
        # Import and register the plugins directly
        import sys
        import os
        from pathlib import Path
        
        # Add the plugins directory to Python path
        current_dir = Path(__file__).parent.parent
        plugins_dir = str(current_dir / "plugins")
        if plugins_dir not in sys.path:
            sys.path.insert(0, plugins_dir)
        
        # Import and register each plugin manually
        from tasks.sample_measurement import SampleMeasurementPlugin
        from services.run_weight_balance import RunWeightBalancePlugin  
        from instruments.weight_balance import WeightBalancePlugin
        
        # Register the plugins
        sample_plugin = SampleMeasurementPlugin()
        service_plugin = RunWeightBalancePlugin()
        instrument_plugin = WeightBalancePlugin()
        
        registry.register_task_plugin(sample_plugin.name, SampleMeasurementPlugin)
        registry.register_service_plugin(service_plugin.name, RunWeightBalancePlugin)
        registry.register_instrument_plugin(instrument_plugin.name, WeightBalancePlugin)
        
        logger.info(f"Plugin system initialized manually. Registered plugins: {registry.list_plugins()}")
        
    except Exception as e:
        logger.error(f"Failed to initialize plugin system: {e}")
        # Fall back to automatic discovery
        try:
            plugin_dirs = [
                str(current_dir / "plugins" / "tasks"),
                str(current_dir / "plugins" / "services"),
                str(current_dir / "plugins" / "instruments")
            ]
            registry.discover_plugins(plugin_dirs)
            logger.info(f"Plugin system initialized via discovery. Registered plugins: {registry.list_plugins()}")
        except Exception as e2:
            logger.error(f"Plugin discovery also failed: {e2}")


# Initialize plugin system when module is imported
initialize_plugin_system()


def build_task_context(task, db) -> Dict[str, Any]:
    """
    Build context information for task execution including previous task results.
    
    Args:
        task: Current task being executed
        db: Database session
        
    Returns:
        Dict containing context information
    """
    context = {
        "workflow_id": task.workflow_id,
        "task_id": task.id,
        "task_name": task.name,
        "previous_task_results": [],
        "previous_tasks": [],
        "database_results": []
    }
    
    try:
        # Get all tasks in the workflow ordered by order_index
        all_tasks = db.query(Task).filter(Task.workflow_id == task.workflow_id).order_by(Task.order_index).all()
        
        # Find previous completed tasks
        previous_tasks = [t for t in all_tasks if t.order_index < task.order_index and t.status == "completed"]
        
        # Add previous task information to context
        for prev_task in previous_tasks:
            task_info = {
                "task_id": prev_task.id,
                "name": prev_task.name,
                "service_parameters": prev_task.service_parameters,
                "status": prev_task.status
            }
            context["previous_tasks"].append(task_info)
            
            # Get results for this task
            result_record = db.query(Result).filter(Result.task_id == prev_task.id).first()
            if result_record:
                result_data = result_record.data
                if isinstance(result_data, str):
                    try:
                        result_data = json.loads(result_data)
                    except:
                        pass
                
                context["previous_task_results"].append({
                    "task_name": prev_task.name,
                    "task_id": prev_task.id,
                    "data": result_data
                })
                
                context["database_results"].append({
                    "task_name": prev_task.name,
                    "task_id": prev_task.id,
                    "data": result_data
                })
    
    except Exception as e:
        logger.warning(f"Failed to build complete context for task {task.id}: {e}")
    
    return context


@celery_app.task(bind=True)
def execute_plugin_workflow(self, workflow_id: int):
    """Execute a workflow using the plugin system."""
    db = SessionLocal()
    
    try:
        # Get workflow and tasks
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return {"status": "error", "message": "Workflow not found"}
        
        logger.info(f"Starting plugin-based workflow execution: {workflow.name} (ID: {workflow_id})")
        
        # Update workflow status
        workflow.status = "running"
        db.commit()
        
        # Get tasks in order
        tasks = sorted(workflow.tasks, key=lambda x: x.order_index)
        
        # Only execute the first task - subsequent tasks will be triggered after completion
        if tasks:
            first_task = tasks[0]
            logger.info(f"Starting first task with plugin system: {first_task.name} (ID: {first_task.id})")
            execute_plugin_task.delay(first_task.id)
            
            # Schedule periodic checks to ensure completion is detected
            complete_workflow.apply_async(args=[workflow_id], countdown=30)
            complete_workflow.apply_async(args=[workflow_id], countdown=60)
            complete_workflow.apply_async(args=[workflow_id], countdown=120)
            complete_workflow.apply_async(args=[workflow_id], countdown=300)
            
            logger.info(f"Plugin-based workflow {workflow_id} started with first task: {first_task.name}")
            return {"status": "running", "workflow_id": workflow_id, "first_task": first_task.name}
        else:
            # No tasks to execute
            workflow.status = "completed"
            db.commit()
            logger.info(f"Workflow {workflow_id} completed (no executable tasks)")
            return {"status": "completed", "workflow_id": workflow_id}
        
    except Exception as e:
        logger.error(f"Plugin workflow {workflow_id} execution error: {str(e)}")
        if workflow:
            workflow.status = "failed"
            db.commit()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True)
def execute_plugin_task(self, task_id: int):
    """Execute a task using the plugin system."""
    db = SessionLocal()
    
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return {"status": "error", "message": "Task not found"}
        
        logger.info(f"Executing task with plugin system: {task.name} (ID: {task_id})")
        
        # Get the appropriate plugin
        registry = get_plugin_registry()
        plugin = registry.get_plugin(task.name)
        
        if not plugin:
            logger.error(f"No plugin found for task: {task.name}")
            task.status = "failed"
            db.commit()
            return {"status": "error", "message": f"No plugin for {task.name}"}
        
        # Build context for the plugin
        context = build_task_context(task, db)
        
        # Get task parameters
        task_params = task.service_parameters
        if isinstance(task_params, str):
            task_params = json.loads(task_params) if task_params else {}
        
        # Execute based on plugin type
        plugin_type = registry.get_plugin_type(task.name)
        result = None
        
        if plugin_type == PluginType.TASK:
            result = execute_task_plugin(task, plugin, task_params, context, db)
        elif plugin_type == PluginType.SERVICE:
            result = execute_service_plugin(task, plugin, task_params, context, db)
        elif plugin_type == PluginType.INSTRUMENT:
            result = execute_instrument_plugin(task, plugin, task_params, context, db)
        else:
            logger.error(f"Unknown plugin type for task: {task.name}")
            task.status = "failed"
            db.commit()
            return {"status": "error", "message": f"Unknown plugin type for {task.name}"}
        
        # If task completed successfully, trigger the next task
        if result and result.get("status") == "completed":
            trigger_next_task(task, db)
        
        return result
        
    except Exception as e:
        logger.error(f"Plugin task {task_id} execution error: {str(e)}")
        if task:
            task.status = "failed"
            db.commit()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


def execute_task_plugin(task, plugin: TaskPlugin, task_params: Dict[str, Any], 
                       context: Dict[str, Any], db) -> Dict[str, Any]:
    """Execute a task plugin (manual tasks)."""
    logger.info(f"Executing task plugin: {plugin.name}")
    
    # Update task status
    initial_status = plugin.get_completion_status(task_params, context)
    task.status = initial_status
    if hasattr(plugin, 'task_type'):
        task.task_type = plugin.task_type
    db.commit()
    
    # Execute the plugin
    result = plugin.execute(task_params, context)
    
    if result.success and result.status == "awaiting_manual_completion":
        logger.info(f"Task {task.id} set to awaiting manual completion")
        return {
            "status": "awaiting_manual",
            "task_id": task.id,
            "message": "Task awaiting manual completion by scientist"
        }
    
    return result.to_dict()


def execute_service_plugin(task, plugin: ServicePlugin, task_params: Dict[str, Any], 
                          context: Dict[str, Any], db) -> Dict[str, Any]:
    """Execute a service plugin."""
    logger.info(f"Executing service plugin: {plugin.name}")
    
    # Update task status
    task.status = "running"
    db.commit()
    
    # Get plugin preparation result
    prep_result = plugin.execute(task_params, context)
    if not prep_result.success:
        task.status = "failed"
        db.commit()
        return prep_result.to_dict()
    
    # Get the prepared request data
    request_data = prep_result.data
    
    try:
        # Make the HTTP request to the service
        endpoint = plugin.get_endpoint()
        action = plugin.get_action()
        timeout = plugin.get_timeout()
        
        logger.info(f"Calling service endpoint: {endpoint}/{action}")
        response = requests.post(f"{endpoint}/{action}", json=request_data, timeout=30)
        
        if response.status_code == 200:
            # Process the service response
            response_data = response.json()
            processed_result = plugin.process_response(response_data)
            
            if processed_result.success:
                # Save results to database
                result_record = Result(task_id=task.id, data=processed_result.data)
                db.add(result_record)
                
                # Update task
                task.status = "completed"
                task.completion_method = "automatic"
                task.completion_timestamp = datetime.now(timezone.utc)
                db.commit()
                
                logger.info(f"Service task {task.id} completed successfully")
                return {
                    "status": "completed",
                    "task_id": task.id,
                    "results": processed_result.data
                }
            else:
                task.status = "failed"
                db.commit()
                return processed_result.to_dict()
        else:
            error_msg = f"Service failed: HTTP {response.status_code}"
            logger.error(f"Task {task.id}: {error_msg}")
            task.status = "failed"
            db.commit()
            return {"status": "failed", "message": error_msg}
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Service request failed: {str(e)}"
        logger.error(f"Task {task.id}: {error_msg}")
        task.status = "failed"
        db.commit()
        return {"status": "failed", "message": error_msg}


def execute_instrument_plugin(task, plugin: InstrumentPlugin, task_params: Dict[str, Any], 
                             context: Dict[str, Any], db) -> Dict[str, Any]:
    """Execute an instrument plugin."""
    logger.info(f"Executing instrument plugin: {plugin.name}")
    
    # Update task status
    task.status = "running"
    db.commit()
    
    # Get plugin preparation result
    prep_result = plugin.execute(task_params, context)
    if not prep_result.success:
        task.status = "failed"
        db.commit()
        return prep_result.to_dict()
    
    # Get the prepared instrument data
    instrument_data = prep_result.data
    
    try:
        endpoint = plugin.get_endpoint()
        action = plugin.get_action()
        timeout = plugin.get_timeout()
        
        # Reset instrument if needed
        if plugin.reset_instrument():
            try:
                requests.post(f"{endpoint}/reset", timeout=10)
                time.sleep(1)
            except:
                logger.warning(f"Could not reset instrument at {endpoint}")
        
        # Start task execution
        logger.info(f"Starting instrument task: {endpoint}/{action}")
        response = requests.post(f"{endpoint}/{action}", json=instrument_data, timeout=30)
        
        if response.status_code not in [200, 202]:
            error_msg = f"Failed to start {plugin.name}: HTTP {response.status_code}"
            logger.error(error_msg)
            task.status = "failed"
            db.commit()
            return {"status": "error", "message": error_msg}
        
        # Check if response contains immediate results (synchronous execution)
        if response.status_code == 200:
            response_data = response.json()
            processed_result = plugin.process_instrument_response(response_data)
            
            if processed_result.success:
                # Save results to database
                result_record = Result(task_id=task.id, data=processed_result.data)
                db.add(result_record)
                
                # Update task
                task.status = "completed"
                task.completion_method = "automatic"
                task.completion_timestamp = datetime.now(timezone.utc)
                db.commit()
                
                logger.info(f"Instrument task {task.id} completed successfully")
                return {
                    "status": "completed", 
                    "task_id": task.id, 
                    "results": processed_result.data
                }
        
        # Monitor asynchronous execution if needed
        if plugin.should_monitor_async():
            return monitor_async_instrument(task, plugin, endpoint, timeout, db)
        
        return {"status": "completed", "task_id": task.id}
        
    except Exception as e:
        error_msg = f"Instrument execution error: {str(e)}"
        logger.error(f"Task {task.id}: {error_msg}")
        task.status = "failed"
        db.commit()
        return {"status": "error", "error": error_msg}


def monitor_async_instrument(task, plugin: InstrumentPlugin, endpoint: str, timeout: int, db):
    """Monitor asynchronous instrument execution."""
    logger.info(f"Task {task.id} started on instrument, monitoring...")
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
                        response_data = results_response.json()
                        processed_result = plugin.process_instrument_response(response_data)
                        
                        if processed_result.success:
                            # Save results to database
                            result_record = Result(task_id=task.id, data=processed_result.data)
                            db.add(result_record)
                            
                            # Update task
                            task.status = "completed"
                            task.completion_method = "automatic"
                            task.completion_timestamp = datetime.now(timezone.utc)
                            db.commit()
                            
                            logger.info(f"Instrument task {task.id} completed successfully")
                            return {
                                "status": "completed", 
                                "task_id": task.id, 
                                "results": processed_result.data
                            }
                
                elif instrument_status in ['failed', 'aborted', 'error']:
                    error_msg = f"Instrument reported {instrument_status}"
                    logger.error(f"Task {task.id}: {error_msg}")
                    task.status = "failed"
                    db.commit()
                    return {"status": "failed", "message": error_msg}
            
            time.sleep(3)
        except requests.exceptions.RequestException as e:
            logger.warning(f"Monitoring error for task {task.id}: {str(e)}")
            time.sleep(5)
    
    # Timeout
    error_msg = "Task execution timeout"
    logger.error(f"Task {task.id}: {error_msg}")
    task.status = "failed"
    db.commit()
    return {"status": "failed", "message": error_msg}


def trigger_next_task(current_task, db):
    """Trigger the next task in sequence after current task completion."""
    try:
        # Get all tasks in the workflow ordered by order_index
        all_tasks = db.query(Task).filter(Task.workflow_id == current_task.workflow_id).order_by(Task.order_index).all()
        
        # Find the current task's position
        current_index = next((i for i, t in enumerate(all_tasks) if t.id == current_task.id), None)
        
        # If there's a next task and it's pending, trigger it
        if current_index is not None and current_index < len(all_tasks) - 1:
            next_task = all_tasks[current_index + 1]
            
            # Only trigger if the next task is pending
            if next_task.status == "pending":
                logger.info(f"Triggering next task in sequence: {next_task.name} (ID: {next_task.id})")
                # Queue the next task for execution
                execute_plugin_task.delay(next_task.id)
    
    except Exception as e:
        logger.error(f"Failed to trigger next task: {e}")


# Import the complete_workflow function from the original workers
from .workers import complete_workflow