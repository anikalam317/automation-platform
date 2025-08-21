from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import os
from pathlib import Path
from datetime import datetime

from ...core.database import get_db
from ...models.database import Service
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/instrument-management", tags=["instrument-management"])

# Paths for definitions
INSTRUMENT_DEFINITIONS_PATH = Path("instrument_definitions")
TASK_DEFINITIONS_PATH = Path("task_definitions")
SERVICE_DEFINITIONS_PATH = Path("service_definitions")
INSTRUMENT_CONFIGS_PATH = Path("instrument_configs")

# Ensure directories exist
INSTRUMENT_DEFINITIONS_PATH.mkdir(exist_ok=True)
TASK_DEFINITIONS_PATH.mkdir(exist_ok=True)
SERVICE_DEFINITIONS_PATH.mkdir(exist_ok=True)
INSTRUMENT_CONFIGS_PATH.mkdir(exist_ok=True)

def _merge_parameters(item_data: Dict[str, Any]) -> Dict[str, Any]:
    """Merge common_parameters and specific_parameters, or return existing parameters"""
    # Handle new structure with common_parameters and specific_parameters
    if 'common_parameters' in item_data or 'specific_parameters' in item_data:
        merged = {}
        merged.update(item_data.get('common_parameters', {}))
        merged.update(item_data.get('specific_parameters', {}))
        return merged
    
    # Handle old structure with just parameters
    return item_data.get('parameters', {})

class InstrumentDefinition(BaseModel):
    id: Optional[str] = None  # Auto-generated if not provided
    name: str
    category: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    description: str
    capabilities: List[str] = []
    parameters: Dict[str, Any] = {}
    connection: Dict[str, Any] = {}
    validation: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}
    typical_runtime_seconds: Optional[int] = None  # Auto-generated if not provided
    status: Optional[str] = None  # Auto-generated if not provided
    created_by: Optional[str] = None  # Auto-generated if not provided
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class TaskDefinition(BaseModel):
    id: Optional[str] = None  # Auto-generated if not provided
    name: str
    category: str
    description: str
    workflow_position: Optional[str] = None  # Auto-generated if not provided
    compatible_instruments: List[str] = []
    parameters: Dict[str, Any] = {}
    quality_checks: Optional[List[str]] = None  # Auto-generated if not provided
    outputs: Optional[List[str]] = None  # Auto-generated if not provided
    prerequisites: Optional[List[str]] = None  # Auto-generated if not provided
    estimated_duration_seconds: Optional[int] = None  # Auto-generated if not provided
    success_criteria: Optional[Dict[str, Any]] = None  # Auto-generated if not provided
    status: Optional[str] = None  # Auto-generated if not provided
    created_by: Optional[str] = None  # Auto-generated if not provided
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@router.get("/instruments", 
            summary="List All Instrument Definitions",
            description="Get all instrument definitions available for scientists to use in workflows")
def list_instruments() -> List[Dict[str, Any]]:
    """List all available instrument definitions"""
    instruments = []
    
    for file_path in INSTRUMENT_DEFINITIONS_PATH.glob("*.json"):
        if file_path.name.startswith("task_"):
            continue  # Skip task definitions
        if file_path.name == "instruments.json":
            continue  # Skip consolidated file, use individual files
            
        try:
            with open(file_path, 'r') as f:
                instrument = json.load(f)
                # Handle both single objects and arrays
                if isinstance(instrument, list):
                    instruments.extend(instrument)
                else:
                    instruments.append(instrument)
        except Exception as e:
            print(f"Error loading instrument {file_path}: {e}")
            continue
    
    return sorted(instruments, key=lambda x: x.get('name', ''))

@router.get("/instruments/{instrument_id}",
            summary="Get Instrument Definition", 
            description="Get detailed definition for a specific instrument")
def get_instrument(instrument_id: str) -> Dict[str, Any]:
    """Get specific instrument definition"""
    file_path = INSTRUMENT_DEFINITIONS_PATH / f"{instrument_id}.json"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Instrument {instrument_id} not found")
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading instrument: {str(e)}")

@router.post("/instruments",
             summary="Create New Instrument Definition",
             description="Create a new instrument definition that will be available in the node palette")
def create_instrument(instrument: InstrumentDefinition) -> Dict[str, str]:
    """Create new instrument definition"""
    
    # Auto-generate required fields if not provided
    if not instrument.id:
        # Generate ID from name
        instrument.id = instrument.name.lower().replace(" ", "-").replace("_", "-")
        # Ensure uniqueness
        counter = 1
        base_id = instrument.id
        while (INSTRUMENT_DEFINITIONS_PATH / f"{instrument.id}.json").exists():
            instrument.id = f"{base_id}-{counter}"
            counter += 1
    
    if not instrument.status:
        instrument.status = "active"
    
    if not instrument.typical_runtime_seconds:
        instrument.typical_runtime_seconds = 300  # Default 5 minutes
    
    # Set timestamps
    now = datetime.utcnow().isoformat() + "Z"
    if not instrument.created_at:
        instrument.created_at = now
    instrument.updated_at = now
    
    # Set default creator
    if not instrument.created_by:
        instrument.created_by = "user"
    
    file_path = INSTRUMENT_DEFINITIONS_PATH / f"{instrument.id}.json"
    
    if file_path.exists():
        raise HTTPException(status_code=400, detail=f"Instrument {instrument.id} already exists")
    
    try:
        # Ensure directory exists
        INSTRUMENT_DEFINITIONS_PATH.mkdir(exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(instrument.dict(), f, indent=2)
        
        return {"message": f"Instrument {instrument.name} created successfully", "id": instrument.id}
        
    except PermissionError:
        raise HTTPException(status_code=500, detail="Permission denied: Cannot create instrument file. Please check file system permissions.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating instrument: {str(e)}")

@router.put("/instruments/{instrument_id}",
            summary="Update Instrument Definition",
            description="Update an existing instrument definition")
def update_instrument(instrument_id: str, instrument: InstrumentDefinition) -> Dict[str, str]:
    """Update existing instrument definition"""
    
    file_path = INSTRUMENT_DEFINITIONS_PATH / f"{instrument_id}.json"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Instrument {instrument_id} not found")
    
    # Update timestamp
    instrument.updated_at = datetime.utcnow().isoformat() + "Z"
    
    try:
        with open(file_path, 'w') as f:
            json.dump(instrument.dict(), f, indent=2)
        
        return {"message": f"Instrument {instrument.name} updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating instrument: {str(e)}")

@router.delete("/instruments/{instrument_id}",
               summary="Delete Instrument Definition",
               description="Delete an instrument definition (only user-created instruments)")
def delete_instrument(instrument_id: str) -> Dict[str, str]:
    """Delete instrument definition"""
    
    file_path = INSTRUMENT_DEFINITIONS_PATH / f"{instrument_id}.json"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Instrument {instrument_id} not found")
    
    try:
        # Check if system-defined (cannot delete)
        with open(file_path, 'r') as f:
            instrument = json.load(f)
            
        if instrument.get('created_by') == 'system':
            raise HTTPException(status_code=403, detail="Cannot delete system-defined instruments")
        
        file_path.unlink()
        
        return {"message": f"Instrument {instrument_id} deleted successfully"}
        
    except PermissionError:
        raise HTTPException(status_code=500, detail="Permission denied: Cannot delete instrument file. The file system may be read-only or you may not have sufficient permissions.")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Instrument file not found: {instrument_id}")
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting instrument: {str(e)}")

@router.get("/tasks",
            summary="List All Task Definitions", 
            description="Get all task definitions available for scientists to use in workflows")
def list_tasks() -> List[Dict[str, Any]]:
    """List all available task definitions"""
    tasks = []
    
    # Read from task_definitions directory, looking for both task_*.json and *.json files
    for file_path in TASK_DEFINITIONS_PATH.glob("*.json"):
        # Skip files that don't contain task definitions
        if file_path.name in ["tasks.json"]:  # Skip consolidated files
            continue
            
        try:
            with open(file_path, 'r') as f:
                task = json.load(f)
                # Only include if it looks like a task definition
                if 'id' in task and 'name' in task:
                    tasks.append(task)
        except Exception as e:
            print(f"Error loading task {file_path}: {e}")
            continue
    
    return sorted(tasks, key=lambda x: x.get('name', ''))

@router.get("/tasks/{task_id}",
            summary="Get Task Definition",
            description="Get detailed definition for a specific task")
def get_task(task_id: str) -> Dict[str, Any]:
    """Get specific task definition"""
    # Try different naming patterns
    possible_files = [
        TASK_DEFINITIONS_PATH / f"task_{task_id}.json",
        TASK_DEFINITIONS_PATH / f"{task_id}.json"
    ]
    
    for file_path in possible_files:
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error loading task: {str(e)}")
    
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@router.post("/tasks",
             summary="Create New Task Definition",
             description="Create a new task definition that will be available in the node palette") 
def create_task(task: TaskDefinition) -> Dict[str, str]:
    """Create new task definition"""
    
    # Auto-generate required fields if not provided
    if not task.id:
        # Generate ID from name
        task.id = task.name.lower().replace(" ", "-").replace("_", "-")
        # Ensure uniqueness
        counter = 1
        base_id = task.id
        while (TASK_DEFINITIONS_PATH / f"task_{task.id}.json").exists():
            task.id = f"{base_id}-{counter}"
            counter += 1
    
    if not task.status:
        task.status = "active"
    
    if not task.workflow_position:
        task.workflow_position = "operation"  # Default position
    
    if not task.estimated_duration_seconds:
        task.estimated_duration_seconds = 300  # Default 5 minutes
    
    if not task.quality_checks:
        task.quality_checks = ["completion_check"]
    
    if not task.outputs:
        task.outputs = ["task_result"]
    
    if not task.prerequisites:
        task.prerequisites = []
    
    if not task.success_criteria:
        task.success_criteria = {"completion": "successful"}
    
    # Set timestamps
    now = datetime.utcnow().isoformat() + "Z"
    if not task.created_at:
        task.created_at = now
    task.updated_at = now
    
    # Set default creator
    if not task.created_by:
        task.created_by = "user"
    
    file_path = TASK_DEFINITIONS_PATH / f"task_{task.id}.json"
    
    if file_path.exists():
        raise HTTPException(status_code=400, detail=f"Task {task.id} already exists")
    
    try:
        # Ensure directory exists
        TASK_DEFINITIONS_PATH.mkdir(exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(task.dict(), f, indent=2)
        
        return {"message": f"Task {task.name} created successfully", "id": task.id}
        
    except PermissionError:
        raise HTTPException(status_code=500, detail="Permission denied: Cannot create task file. Please check file system permissions.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")

@router.put("/tasks/{task_id}",
            summary="Update Task Definition",
            description="Update an existing task definition")
def update_task(task_id: str, task: TaskDefinition) -> Dict[str, str]:
    """Update existing task definition"""
    
    file_path = TASK_DEFINITIONS_PATH / f"task_{task_id}.json"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Update timestamp
    task.updated_at = datetime.utcnow().isoformat() + "Z"
    
    try:
        with open(file_path, 'w') as f:
            json.dump(task.dict(), f, indent=2)
        
        return {"message": f"Task {task.name} updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")

@router.delete("/tasks/{task_id}",
               summary="Delete Task Definition", 
               description="Delete a task definition (only user-created tasks)")
def delete_task(task_id: str) -> Dict[str, str]:
    """Delete task definition"""
    
    file_path = TASK_DEFINITIONS_PATH / f"task_{task_id}.json"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    try:
        # Check if system-defined (cannot delete)
        with open(file_path, 'r') as f:
            task = json.load(f)
            
        if task.get('created_by') == 'system':
            raise HTTPException(status_code=403, detail="Cannot delete system-defined tasks")
        
        file_path.unlink()
        
        return {"message": f"Task {task_id} deleted successfully"}
        
    except PermissionError:
        raise HTTPException(status_code=500, detail="Permission denied: Cannot delete task file. The file system may be read-only or you may not have sufficient permissions.")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Task file not found: {task_id}")
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")

@router.patch("/instruments/{instrument_id}/disable",
              summary="Disable Instrument Definition",
              description="Mark an instrument as inactive (soft delete)")
def disable_instrument(instrument_id: str) -> Dict[str, str]:
    """Mark instrument as inactive instead of deleting"""
    
    file_path = INSTRUMENT_DEFINITIONS_PATH / f"{instrument_id}.json"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Instrument {instrument_id} not found")
    
    try:
        # Read current data
        with open(file_path, 'r') as f:
            instrument = json.load(f)
        
        # Mark as inactive
        instrument['status'] = 'inactive'
        instrument['updated_at'] = datetime.utcnow().isoformat() + "Z"
        
        # Write back
        with open(file_path, 'w') as f:
            json.dump(instrument, f, indent=2)
        
        return {"message": f"Instrument {instrument_id} marked as inactive"}
        
    except PermissionError:
        raise HTTPException(status_code=500, detail="Permission denied: Cannot modify instrument file. The file system may be read-only.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disabling instrument: {str(e)}")

@router.patch("/tasks/{task_id}/disable",
              summary="Disable Task Definition",
              description="Mark a task as inactive (soft delete)")
def disable_task(task_id: str) -> Dict[str, str]:
    """Mark task as inactive instead of deleting"""
    
    file_path = TASK_DEFINITIONS_PATH / f"task_{task_id}.json"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    try:
        # Read current data
        with open(file_path, 'r') as f:
            task = json.load(f)
        
        # Mark as inactive
        task['status'] = 'inactive'
        task['updated_at'] = datetime.utcnow().isoformat() + "Z"
        
        # Write back
        with open(file_path, 'w') as f:
            json.dump(task, f, indent=2)
        
        return {"message": f"Task {task_id} marked as inactive"}
        
    except PermissionError:
        raise HTTPException(status_code=500, detail="Permission denied: Cannot modify task file. The file system may be read-only.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disabling task: {str(e)}")

@router.get("/node-palette", 
            summary="Get Node Palette Data",
            description="Get all instruments, tasks, and services formatted for the frontend node palette")
def get_node_palette_data(db: Session = Depends(get_db)) -> Dict[str, List[Dict[str, Any]]]:
    """Get node palette data for frontend"""
    
    instruments = list_instruments()
    tasks = list_tasks()
    
    # Get services from database
    services = db.query(Service).filter(Service.enabled == True).all()
    
    # Format for node palette
    palette_data = {
        "instruments": [
            {
                "id": inst["id"],
                "name": inst["name"],
                "category": inst["category"],
                "description": inst["description"],
                "parameters": _merge_parameters(inst),  # Keep for backwards compatibility
                "common_parameters": inst.get("common_parameters", {}),  # Preserve original structure
                "specific_parameters": inst.get("specific_parameters", {}),  # Preserve original structure
                "typical_runtime": inst["typical_runtime_seconds"],
                "capabilities": inst.get("capabilities", [])
            }
            for inst in instruments if inst.get("status") == "active"
        ],
        "tasks": [
            {
                "id": task["id"],
                "name": task["name"],
                "category": task["category"], 
                "description": task["description"],
                "parameters": _merge_parameters(task),  # Keep for backwards compatibility
                "common_parameters": task.get("common_parameters", {}),  # Preserve original structure
                "specific_parameters": task.get("specific_parameters", {}),  # Preserve original structure
                "estimated_duration": task.get("estimated_duration_seconds", 300),
                "workflow_position": task.get("workflow_position", "operation")
            }
            for task in tasks if task.get("status") == "active"
        ],
        "services": [
            {
                "id": str(service.id),
                "name": service.name,
                "description": service.description,
                "type": service.type,
                "endpoint": service.endpoint,
                "parameters": service.default_parameters or {},
                "enabled": service.enabled
            }
            for service in services
        ]
    }
    
    return palette_data

@router.post("/sync-to-database",
             summary="Sync Definitions to Database",
             description="Sync instrument and task definitions to the database for workflow execution")
def sync_definitions_to_database(db: Session = Depends(get_db)) -> Dict[str, str]:
    """Sync definitions to database services and task_templates tables"""
    
    try:
        instruments = list_instruments()
        synced_count = 0
        
        for instrument in instruments:
            # Check if service already exists
            existing_service = db.query(Service).filter(
                Service.name == instrument["name"]
            ).first()
            
            if not existing_service:
                # Create new service
                service = Service(
                    name=instrument["name"],
                    type=instrument["connection"]["type"],
                    endpoint=instrument["connection"]["simulation_endpoint"],
                    default_parameters=instrument["parameters"]
                )
                db.add(service)
                synced_count += 1
        
        db.commit()
        
        return {"message": f"Synced {synced_count} definitions to database"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error syncing to database: {str(e)}")