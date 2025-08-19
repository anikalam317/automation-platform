from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
import os

from ...core.database import get_db
from ...models.database import Workflow, Task
from ...schemas.workflow import WorkflowCreate, WorkflowResponse, WorkflowUpdate

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# Environment-aware URLs
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")
SAMPLE_PREP_URL = os.getenv("SAMPLE_PREP_URL", "http://localhost:5002") 
HPLC_URL = os.getenv("HPLC_URL", "http://localhost:5003")


@router.post("/", response_model=WorkflowResponse, status_code=201, 
            summary="Create New Workflow",
            description="""
Create a new laboratory workflow with automatic task-to-service mapping.

**Important**: Workflows are created in 'pending' status and **require manual execution**.
Use the `/api/workflows/{workflow_id}/execute-celery` endpoint to start execution.

### Automatic Service Mapping
The system automatically maps task names to lab instruments:
- **Sample Preparation** / **Sample Preparation Station** → Sample Prep Station (Service ID 1)
- **HPLC Analysis System** / **HPLC Purity Analysis** → HPLC System (Service ID 2)

### Default Parameters
Each task receives default parameters based on its type:
- **Sample Preparation**: volume=10.0mL, dilution_factor=2.0, target_ph=7.0, timeout=300s
- **HPLC Analysis**: method=USP_assay_method, injection_volume=10.0µL, runtime_minutes=20.0, timeout=1800s

### Frontend Integration
When created via frontend, tasks may include service_id and service_parameters which are preserved.
""")
def create_workflow(workflow: WorkflowCreate, db: Session = Depends(get_db)):
    # DEBUG: Print incoming workflow data  
    print(f"DEBUG: Creating workflow - Name: {workflow.name}, Author: {workflow.author}")
    print(f"DEBUG: Number of tasks: {len(workflow.tasks)}")
    for i, task in enumerate(workflow.tasks):
        print(f"DEBUG: Task {i}: {task}")
        print(f"DEBUG: Task {i} type: {type(task)}")
        if isinstance(task, dict):
            print(f"DEBUG: Task {i} keys: {list(task.keys())}")
    
    db_workflow = Workflow(name=workflow.name, author=workflow.author, status="pending")
    db.add(db_workflow)
    db.flush()  # Get the ID without committing

    # Task name to service mapping for automatic execution
    task_service_mapping = {
        "Sample Preparation": {
            "service_id": 1,  # Sample Preparation Station
            "default_params": {
                "volume": 10.0,
                "dilution_factor": 2.0,
                "target_ph": 7.0,
                "timeout": 300
            }
        },
        "Sample Preparation Station": {
            "service_id": 1,  # Sample Preparation Station
            "default_params": {
                "volume": 10.0,
                "dilution_factor": 2.0,
                "target_ph": 7.0,
                "timeout": 300
            }
        },
        "HPLC Purity Analysis": {
            "service_id": 2,  # HPLC Analysis System
            "default_params": {
                "method": "USP_assay_method",
                "injection_volume": 10.0,
                "runtime_minutes": 20.0,
                "timeout": 1800
            }
        },
        "HPLC Analysis System": {
            "service_id": 2,  # HPLC Analysis System
            "default_params": {
                "method": "USP_assay_method",
                "injection_volume": 10.0,
                "runtime_minutes": 20.0,
                "timeout": 1800
            }
        },
        "HPLC System": {
            "service_id": 2,  # HPLC Analysis System
            "default_params": {
                "method": "USP_assay_method",
                "injection_volume": 10.0,
                "runtime_minutes": 20.0,
                "timeout": 1800
            }
        }
    }

    for i, task_data in enumerate(workflow.tasks):
        task_name = task_data["name"]
        print(f"DEBUG: Processing task {i}: '{task_name}'")
        print(f"DEBUG: Frontend sent service_id: {task_data.get('service_id')}")
        print(f"DEBUG: Frontend sent service_parameters: {task_data.get('service_parameters')}")
        
        # Get frontend service_id if provided, otherwise auto-map
        service_id = task_data.get('service_id')
        service_parameters = task_data.get('service_parameters')
        
        print(f"DEBUG: Checking if '{task_name}' is in mapping: {task_name in task_service_mapping}")
        print(f"DEBUG: Available mapping keys: {list(task_service_mapping.keys())}")
        
        # Only auto-map if service_id not provided by frontend
        if not service_id:
            # Try exact match first
            mapping_key = None
            if task_name in task_service_mapping:
                mapping_key = task_name
                print(f"DEBUG: Found exact match: '{task_name}'")
            else:
                # Try case-insensitive match
                task_name_lower = task_name.lower()
                for key in task_service_mapping.keys():
                    if key.lower() == task_name_lower:
                        mapping_key = key
                        print(f"DEBUG: Found case-insensitive match: '{task_name}' -> '{key}'")
                        break
            
            if mapping_key:
                mapping = task_service_mapping[mapping_key]
                service_id = mapping["service_id"]
                print(f"DEBUG: Auto-mapped '{task_name}' to service_id: {service_id}")
                
                # Create parameters with unique sample ID
                params = mapping["default_params"].copy()
                params["sample_id"] = f"WF{db_workflow.id}_T{i+1}_{workflow.name}".replace(" ", "_")
                service_parameters = params
            else:
                print(f"DEBUG: No mapping found for task: '{task_name}'")
        else:
            print(f"DEBUG: Using frontend-provided service_id: {service_id}")
            # If frontend provides service_id but no parameters, use default parameters
            if not service_parameters:
                # Try to find matching task template to get default parameters
                mapping_key = None
                if task_name in task_service_mapping:
                    mapping_key = task_name
                else:
                    task_name_lower = task_name.lower()
                    for key in task_service_mapping.keys():
                        if key.lower() == task_name_lower:
                            mapping_key = key
                            break
                
                if mapping_key:
                    mapping = task_service_mapping[mapping_key]
                    params = mapping["default_params"].copy()
                    params["sample_id"] = f"WF{db_workflow.id}_T{i+1}_{workflow.name}".replace(" ", "_")
                    service_parameters = params
                    print(f"DEBUG: Applied default parameters for '{task_name}': {service_parameters}")
        
        db_task = Task(
            name=task_name,
            workflow_id=db_workflow.id,
            order_index=i,
            status="pending",
            service_id=service_id,
            service_parameters=service_parameters,
        )
        print(f"DEBUG: Created task with service_id: {service_id}, parameters: {service_parameters}")
        db.add(db_task)

    db.commit()
    db.refresh(db_workflow)
    
    # Workflow created successfully, but not executed automatically
    # Execution must be triggered manually via the execute endpoint
    print(f"Workflow {db_workflow.id} created successfully. Use the execute endpoint to start execution.")
    
    return db_workflow


@router.get("/", response_model=List[WorkflowResponse],
           summary="List All Workflows",
           description="""
Get a list of all workflows ordered by creation date (newest first).

### Response Information
Each workflow includes:
- **Basic Information**: ID, name, author, creation/update timestamps
- **Status**: pending, running, completed, failed, paused, stopped
- **Tasks**: Complete list of tasks with their status and results
- **Service Mapping**: Shows which instruments are assigned to each task

### Workflow Status Meanings
- **pending**: Created but not yet executed (requires manual trigger)
- **running**: Currently executing via Celery workers
- **completed**: All tasks finished successfully
- **failed**: One or more tasks failed during execution
- **paused**: Execution temporarily suspended
- **stopped**: Execution permanently halted

### Task Information
For each task, you'll see:
- Service mapping (which instrument will execute it)
- Current status and progress
- Results data (when completed)
- Service parameters used for execution
""")
def get_workflows(db: Session = Depends(get_db)):
    workflows = db.query(Workflow).order_by(Workflow.created_at.desc()).all()
    return workflows


@router.get("/{workflow_id}", response_model=WorkflowResponse,
           summary="Get Workflow Details", 
           description="""
Get detailed information for a specific workflow including all tasks and results.

### Real-time Status Monitoring
This endpoint provides real-time workflow status including:
- **Current workflow status** (pending/running/completed/failed)
- **Individual task status** for each step in the workflow
- **Execution progress** and timing information
- **Complete results data** for finished tasks

### Task Results
For completed tasks, you'll receive detailed analytical data:
- **Sample Preparation Results**: recovery %, pH, volume, quality checks
- **HPLC Analysis Results**: purity %, peak data, chromatograms, quality assessment

### Usage for Monitoring
Poll this endpoint every 2-3 seconds during workflow execution to get live updates.
Alternatively, use WebSocket connections for real-time push notifications.

### Frontend Integration
This is the primary endpoint used by the frontend Monitor tab for live workflow tracking.
""")
def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(
    workflow_id: int, workflow_update: WorkflowUpdate, db: Session = Depends(get_db)
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow_update.name is not None:
        workflow.name = workflow_update.name
    if workflow_update.status is not None:
        workflow.status = workflow_update.status

    db.commit()
    db.refresh(workflow)
    return workflow


@router.post("/{workflow_id}/pause")
def pause_workflow(workflow_id: int, db: Session = Depends(get_db)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow.status == "running":
        workflow.status = "paused"
        workflow.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {"message": "Workflow paused successfully", "status": "paused"}
    else:
        raise HTTPException(status_code=400, detail=f"Cannot pause workflow with status: {workflow.status}")


@router.post("/{workflow_id}/stop")
def stop_workflow(workflow_id: int, db: Session = Depends(get_db)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow.status in ["running", "paused"]:
        workflow.status = "stopped"
        workflow.updated_at = datetime.now(timezone.utc)
        
        # Stop all running tasks
        running_tasks = db.query(Task).filter(
            Task.workflow_id == workflow_id,
            Task.status == "running"
        ).all()
        for task in running_tasks:
            task.status = "stopped"
        
        db.commit()
        return {"message": "Workflow stopped successfully", "status": "stopped"}
    else:
        raise HTTPException(status_code=400, detail=f"Cannot stop workflow with status: {workflow.status}")


@router.post("/{workflow_id}/resume")
def resume_workflow(workflow_id: int, db: Session = Depends(get_db)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow.status == "paused":
        workflow.status = "running"
        workflow.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {"message": "Workflow resumed successfully", "status": "running"}
    else:
        raise HTTPException(status_code=400, detail=f"Cannot resume workflow with status: {workflow.status}")


@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: int, db: Session = Depends(get_db)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Delete workflow (tasks and results will be cascade deleted)
    db.delete(workflow)
    db.commit()
    return {"message": "Workflow deleted successfully"}


@router.post("/execute-concurrent",
            summary="Execute Multiple Workflows Concurrently",
            description="""
Execute multiple workflows simultaneously using Celery group execution.

### Use Cases
- **Parallel Experiments**: Analyze multiple samples with identical protocols
- **Load Testing**: Validate system performance under concurrent workload
- **Batch Processing**: High-throughput analysis of multiple samples

### Execution Model
- All specified workflows are launched simultaneously as a Celery group
- Each workflow executes independently with its own task chain
- System can handle concurrent instrument access through queue management
- Individual workflow failures don't affect others in the group

### Response
Returns a Celery group task ID for monitoring the entire batch execution.

### Scaling
Scale Celery workers for higher concurrency:
```bash
docker compose -f compose_v1.yml up worker --scale worker=4 -d
```

### Monitoring Concurrent Execution
- Use individual workflow endpoints to monitor each workflow
- Check Celery worker logs for distributed execution details
- Monitor instrument utilization through instrument status endpoints
""")
def execute_concurrent_workflows(workflow_ids: list[int], db: Session = Depends(get_db)):
    from ...tasks.workers import execute_concurrent_workflows
    
    # Validate all workflows exist
    existing_workflows = db.query(Workflow).filter(Workflow.id.in_(workflow_ids)).all()
    if len(existing_workflows) != len(workflow_ids):
        raise HTTPException(status_code=404, detail="One or more workflows not found")
    
    try:
        # Launch concurrent execution via Celery
        result = execute_concurrent_workflows.delay(workflow_ids)
        return {
            "message": f"Started concurrent execution of {len(workflow_ids)} workflows",
            "celery_task_id": result.id,
            "workflow_ids": workflow_ids
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start concurrent execution: {str(e)}")


@router.post("/{workflow_id}/execute-celery",
            summary="Execute Workflow (Manual Trigger)",
            description="""
**Execute a workflow via Celery task queue** - This is the primary execution method.

### Execution Process
1. Workflow status changes to 'running'
2. Tasks are queued for sequential execution using Celery chains
3. Each task is mapped to its corresponding lab instrument
4. Instruments are reset, then execution begins with real-time monitoring
5. Results are captured and stored in the database
6. Workflow status is updated to 'completed' or 'failed'

### Typical Execution Times
- **Sample Preparation**: 60-90 seconds (dilution, pH adjustment, filtration)
- **HPLC Analysis**: 80-120 seconds (equilibration, injection, separation, processing)

### Monitoring
Use the following endpoints to monitor progress:
- `GET /api/workflows/{workflow_id}` - Get workflow and task status
- `GET /api/tasks/{task_id}` - Get individual task details and results

### Error Handling
- If a task fails, the workflow status becomes 'failed'
- Subsequent tasks in the chain are not executed
- Use workflow control endpoints to pause/stop/resume execution

### Concurrent Execution
Multiple workflows can run simultaneously using separate Celery workers.
""")
def execute_workflow_via_celery(workflow_id: int, db: Session = Depends(get_db)):
    from ...tasks.workers import execute_workflow
    
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    try:
        # Launch via Celery
        result = execute_workflow.delay(workflow_id)
        return {
            "message": f"Workflow {workflow_id} queued for execution",
            "celery_task_id": result.id,
            "workflow_name": workflow.name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue workflow: {str(e)}")
