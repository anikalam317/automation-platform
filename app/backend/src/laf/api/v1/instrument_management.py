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

# Paths for instrument definitions
INSTRUMENT_DEFINITIONS_PATH = Path("instrument_definitions")
INSTRUMENT_CONFIGS_PATH = Path("instrument_configs")

# Ensure directories exist
INSTRUMENT_DEFINITIONS_PATH.mkdir(exist_ok=True)
INSTRUMENT_CONFIGS_PATH.mkdir(exist_ok=True)

class InstrumentDefinition(BaseModel):
    id: str
    name: str
    category: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    description: str
    capabilities: List[str]
    parameters: Dict[str, Any]
    connection: Dict[str, Any]
    validation: Dict[str, Any]
    outputs: Dict[str, Any]
    typical_runtime_seconds: int
    status: str = "active"
    created_by: str = "user"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class TaskDefinition(BaseModel):
    id: str
    name: str
    category: str
    description: str
    workflow_position: str
    compatible_instruments: List[str]
    parameters: Dict[str, Any]
    quality_checks: List[str]
    outputs: List[str]
    prerequisites: List[str]
    estimated_duration_seconds: int
    success_criteria: Dict[str, Any]
    status: str = "active"
    created_by: str = "user"
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
            
        try:
            with open(file_path, 'r') as f:
                instrument = json.load(f)
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
    
    # Set timestamps
    now = datetime.utcnow().isoformat() + "Z"
    instrument.created_at = now
    instrument.updated_at = now
    
    file_path = INSTRUMENT_DEFINITIONS_PATH / f"{instrument.id}.json"
    
    if file_path.exists():
        raise HTTPException(status_code=400, detail=f"Instrument {instrument.id} already exists")
    
    try:
        with open(file_path, 'w') as f:
            json.dump(instrument.dict(), f, indent=2)
        
        return {"message": f"Instrument {instrument.name} created successfully", "id": instrument.id}
        
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting instrument: {str(e)}")

@router.get("/tasks",
            summary="List All Task Definitions", 
            description="Get all task definitions available for scientists to use in workflows")
def list_tasks() -> List[Dict[str, Any]]:
    """List all available task definitions"""
    tasks = []
    
    for file_path in INSTRUMENT_DEFINITIONS_PATH.glob("task_*.json"):
        try:
            with open(file_path, 'r') as f:
                task = json.load(f)
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
    file_path = INSTRUMENT_DEFINITIONS_PATH / f"task_{task_id}.json"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading task: {str(e)}")

@router.post("/tasks",
             summary="Create New Task Definition",
             description="Create a new task definition that will be available in the node palette") 
def create_task(task: TaskDefinition) -> Dict[str, str]:
    """Create new task definition"""
    
    # Set timestamps
    now = datetime.utcnow().isoformat() + "Z"
    task.created_at = now
    task.updated_at = now
    
    file_path = INSTRUMENT_DEFINITIONS_PATH / f"task_{task.id}.json"
    
    if file_path.exists():
        raise HTTPException(status_code=400, detail=f"Task {task.id} already exists")
    
    try:
        with open(file_path, 'w') as f:
            json.dump(task.dict(), f, indent=2)
        
        return {"message": f"Task {task.name} created successfully", "id": task.id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")

@router.put("/tasks/{task_id}",
            summary="Update Task Definition",
            description="Update an existing task definition")
def update_task(task_id: str, task: TaskDefinition) -> Dict[str, str]:
    """Update existing task definition"""
    
    file_path = INSTRUMENT_DEFINITIONS_PATH / f"task_{task_id}.json"
    
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
    
    file_path = INSTRUMENT_DEFINITIONS_PATH / f"task_{task_id}.json"
    
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")

@router.get("/node-palette", 
            summary="Get Node Palette Data",
            description="Get all instruments and tasks formatted for the frontend node palette")
def get_node_palette_data() -> Dict[str, List[Dict[str, Any]]]:
    """Get node palette data for frontend"""
    
    instruments = list_instruments()
    tasks = list_tasks()
    
    # Format for node palette
    palette_data = {
        "instruments": [
            {
                "id": inst["id"],
                "name": inst["name"],
                "category": inst["category"],
                "description": inst["description"],
                "parameters": inst["parameters"],
                "typical_runtime": inst["typical_runtime_seconds"],
                "capabilities": inst["capabilities"]
            }
            for inst in instruments if inst.get("status") == "active"
        ],
        "tasks": [
            {
                "id": task["id"],
                "name": task["name"],
                "category": task["category"], 
                "description": task["description"],
                "parameters": task["parameters"],
                "estimated_duration": task["estimated_duration_seconds"],
                "workflow_position": task["workflow_position"]
            }
            for task in tasks if task.get("status") == "active"
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