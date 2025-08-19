"""
Simple demo backend for testing the frontend
This provides the essential API endpoints needed for the frontend to work
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

app = FastAPI(
    title="Laboratory Automation Framework - Demo API",
    description="Demo backend for testing the frontend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo
workflows_db = []
tasks_db = []

# Task Templates - preconfigured task types that can be reused
task_templates_db = [
    {
        "id": 1,
        "name": "HPLC Analysis",
        "description": "High Performance Liquid Chromatography analysis",
        "category": "analytical",
        "type": "hplc",
        "required_service_type": "hplc",
        "default_parameters": {
            "column": "C18",
            "flow_rate": "1.0 mL/min",
            "temperature": "30°C",
            "injection_volume": "10µL"
        },
        "estimated_duration": 30,  # minutes
        "enabled": True
    },
    {
        "id": 2,
        "name": "Sample Preparation",
        "description": "Automated sample preparation and dilution",
        "category": "preparative",
        "type": "sample-prep",
        "required_service_type": "liquid-handler",
        "default_parameters": {
            "dilution_factor": 10,
            "solvent": "methanol",
            "volume": "1mL"
        },
        "estimated_duration": 15,
        "enabled": True
    },
    {
        "id": 3,
        "name": "GC-MS Analysis",
        "description": "Gas Chromatography Mass Spectrometry analysis",
        "category": "analytical", 
        "type": "gc-ms",
        "required_service_type": "gc-ms",
        "default_parameters": {
            "injection_temp": "250°C",
            "oven_program": "40°C-300°C",
            "scan_range": "50-500 m/z"
        },
        "estimated_duration": 45,
        "enabled": True
    },
    {
        "id": 4,
        "name": "Data Processing",
        "description": "Automated data analysis and reporting",
        "category": "processing",
        "type": "data-analysis",
        "required_service_type": None,  # Software-based, no physical instrument
        "default_parameters": {
            "analysis_type": "quantitative",
            "report_format": "PDF",
            "include_graphs": True
        },
        "estimated_duration": 10,
        "enabled": True
    }
]

# Services/Instruments - physical equipment
services_db = [
    {
        "id": 1,
        "name": "HPLC System A",
        "description": "High Performance Liquid Chromatography",
        "type": "hplc",
        "endpoint": "http://localhost:8001/hplc",
        "enabled": True,
        "default_parameters": {
            "column": "C18",
            "flow_rate": "1.0 mL/min",
            "temperature": "30°C"
        }
    },
    {
        "id": 2,
        "name": "GC-MS System",
        "description": "Gas Chromatography Mass Spectrometry",
        "type": "gc-ms",
        "endpoint": "http://localhost:8002/gcms",
        "enabled": True,
        "default_parameters": {
            "injection_temp": "250°C",
            "oven_program": "custom"
        }
    },
    {
        "id": 3,
        "name": "Liquid Handler",
        "description": "Automated liquid handling system",
        "type": "liquid-handler",
        "endpoint": "http://localhost:8003/liquidhandler",
        "enabled": True,
        "default_parameters": {
            "tip_type": "1000µL",
            "aspiration_speed": "medium"
        }
    }
]

# Pydantic models
class WorkflowCreate(BaseModel):
    name: str
    author: str
    tasks: List[Dict[str, Any]] = []

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    results: Optional[Dict[str, Any]] = None

class WorkflowGenerationRequest(BaseModel):
    prompt: str

class TaskTemplateCreate(BaseModel):
    name: str
    description: str
    category: str
    type: str
    required_service_type: Optional[str] = None
    default_parameters: Dict[str, Any] = {}
    estimated_duration: int = 30  # minutes
    enabled: bool = True

class TaskTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    required_service_type: Optional[str] = None
    default_parameters: Optional[Dict[str, Any]] = None
    estimated_duration: Optional[int] = None
    enabled: Optional[bool] = None

class ServiceCreate(BaseModel):
    name: str
    description: str
    type: str
    endpoint: str
    default_parameters: Dict[str, Any] = {}
    enabled: bool = True

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    endpoint: Optional[str] = None
    default_parameters: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None

# Workflow endpoints
@app.get("/api/workflows")
def get_workflows():
    return workflows_db

@app.post("/api/workflows")
def create_workflow(workflow: WorkflowCreate):
    workflow_id = len(workflows_db) + 1
    
    # Create workflow
    new_workflow = {
        "id": workflow_id,
        "name": workflow.name,
        "author": workflow.author,
        "status": "pending",
        "workflow_hash": f"hash_{workflow_id}",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "tasks": []
    }
    
    # Create tasks
    for i, task_data in enumerate(workflow.tasks):
        task_id = len(tasks_db) + 1
        new_task = {
            "id": task_id,
            "name": task_data["name"],
            "workflow_id": workflow_id,
            "service_id": task_data.get("service_id"),
            "service_parameters": task_data.get("service_parameters"),
            "status": "pending",
            "order_index": i,
            "executed_at": datetime.now().isoformat(),
            "results": []
        }
        tasks_db.append(new_task)
        new_workflow["tasks"].append(new_task)
    
    workflows_db.append(new_workflow)
    return new_workflow

@app.get("/api/workflows/{workflow_id}")
def get_workflow(workflow_id: int):
    workflow = next((w for w in workflows_db if w["id"] == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Add tasks to workflow
    workflow_tasks = [t for t in tasks_db if t["workflow_id"] == workflow_id]
    workflow["tasks"] = sorted(workflow_tasks, key=lambda x: x["order_index"])
    
    return workflow

@app.put("/api/workflows/{workflow_id}")
def update_workflow(workflow_id: int, workflow_update: WorkflowUpdate):
    workflow = next((w for w in workflows_db if w["id"] == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow_update.name is not None:
        workflow["name"] = workflow_update.name
    if workflow_update.status is not None:
        workflow["status"] = workflow_update.status
    
    workflow["updated_at"] = datetime.now().isoformat()
    return workflow

# Task endpoints
@app.get("/api/tasks/{task_id}")
def get_task(task_id: int):
    task = next((t for t in tasks_db if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, task_update: TaskUpdate):
    task = next((t for t in tasks_db if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task_update.status is not None:
        task["status"] = task_update.status
    if task_update.results is not None:
        task["results"].append({
            "id": len(task["results"]) + 1,
            "task_id": task_id,
            "data": task_update.results,
            "created_at": datetime.now().isoformat()
        })
    
    return task

# Service endpoints
@app.get("/api/services")
def get_services():
    return services_db

@app.get("/api/services/{service_id}")
def get_service(service_id: int):
    service = next((s for s in services_db if s["id"] == service_id), None)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

@app.post("/api/services")
def create_service(service: ServiceCreate):
    service_id = len(services_db) + 1
    new_service = {
        "id": service_id,
        "name": service.name,
        "description": service.description,
        "type": service.type,
        "endpoint": service.endpoint,
        "default_parameters": service.default_parameters,
        "enabled": service.enabled
    }
    services_db.append(new_service)
    return new_service

@app.put("/api/services/{service_id}")
def update_service(service_id: int, service_update: ServiceUpdate):
    service = next((s for s in services_db if s["id"] == service_id), None)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if service_update.name is not None:
        service["name"] = service_update.name
    if service_update.description is not None:
        service["description"] = service_update.description
    if service_update.type is not None:
        service["type"] = service_update.type
    if service_update.endpoint is not None:
        service["endpoint"] = service_update.endpoint
    if service_update.default_parameters is not None:
        service["default_parameters"] = service_update.default_parameters
    if service_update.enabled is not None:
        service["enabled"] = service_update.enabled
    
    return service

@app.delete("/api/services/{service_id}")
def delete_service(service_id: int):
    global services_db
    service = next((s for s in services_db if s["id"] == service_id), None)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    services_db = [s for s in services_db if s["id"] != service_id]
    return {"message": "Service deleted successfully"}

# Task Template endpoints
@app.get("/api/task-templates")
def get_task_templates():
    return task_templates_db

@app.post("/api/task-templates")
def create_task_template(template: TaskTemplateCreate):
    template_id = len(task_templates_db) + 1
    new_template = {
        "id": template_id,
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "type": template.type,
        "required_service_type": template.required_service_type,
        "default_parameters": template.default_parameters,
        "estimated_duration": template.estimated_duration,
        "enabled": template.enabled
    }
    task_templates_db.append(new_template)
    return new_template

@app.get("/api/task-templates/{template_id}")
def get_task_template(template_id: int):
    template = next((t for t in task_templates_db if t["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Task template not found")
    return template

@app.put("/api/task-templates/{template_id}")
def update_task_template(template_id: int, template_update: TaskTemplateUpdate):
    template = next((t for t in task_templates_db if t["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Task template not found")
    
    if template_update.name is not None:
        template["name"] = template_update.name
    if template_update.description is not None:
        template["description"] = template_update.description
    if template_update.category is not None:
        template["category"] = template_update.category
    if template_update.type is not None:
        template["type"] = template_update.type
    if template_update.required_service_type is not None:
        template["required_service_type"] = template_update.required_service_type
    if template_update.default_parameters is not None:
        template["default_parameters"] = template_update.default_parameters
    if template_update.estimated_duration is not None:
        template["estimated_duration"] = template_update.estimated_duration
    if template_update.enabled is not None:
        template["enabled"] = template_update.enabled
    
    return template

@app.delete("/api/task-templates/{template_id}")
def delete_task_template(template_id: int):
    global task_templates_db
    template = next((t for t in task_templates_db if t["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Task template not found")
    
    task_templates_db = [t for t in task_templates_db if t["id"] != template_id]
    return {"message": "Task template deleted successfully"}

# AI workflow generation
@app.post("/api/ai/generate-workflow")
def generate_workflow(request: WorkflowGenerationRequest):
    prompt = request.prompt.lower()
    
    # Simple pattern matching for demo
    if "hplc" in prompt or "chromatography" in prompt:
        tasks = [
            {
                "name": "Sample Preparation",
                "service_id": 3,  # Liquid Handler
                "service_parameters": {
                    "dilution_factor": 10,
                    "solvent": "methanol",
                    "volume": "1mL"
                }
            },
            {
                "name": "HPLC Analysis",
                "service_id": 1,  # HPLC
                "service_parameters": {
                    "method": "gradient_method_1",
                    "injection_volume": "10µL",
                    "column_temp": "30°C",
                    "flow_rate": "1.0mL/min"
                }
            },
            {
                "name": "Data Processing",
                "service_parameters": {
                    "analysis_type": "quantitative",
                    "report_format": "PDF"
                }
            }
        ]
        name = "HPLC Analysis Workflow"
    
    elif "gc-ms" in prompt or "gas chromatography" in prompt:
        tasks = [
            {
                "name": "Sample Extraction",
                "service_id": 3,  # Liquid Handler
                "service_parameters": {
                    "extraction_method": "liquid-liquid",
                    "solvent": "hexane",
                    "volume": "2mL"
                }
            },
            {
                "name": "GC-MS Analysis",
                "service_id": 2,  # GC-MS
                "service_parameters": {
                    "method": "volatiles_screening",
                    "injection_mode": "splitless",
                    "oven_program": "40°C-300°C"
                }
            },
            {
                "name": "Data Analysis",
                "service_parameters": {
                    "library_search": "NIST",
                    "report_format": "PDF"
                }
            }
        ]
        name = "GC-MS Analysis Workflow"
    
    elif "pharmaceutical" in prompt:
        tasks = [
            {
                "name": "Sample Weighing",
                "service_parameters": {
                    "target_weight": "100mg",
                    "tolerance": "±1mg"
                }
            },
            {
                "name": "Sample Dissolution",
                "service_id": 3,
                "service_parameters": {
                    "solvent": "methanol/water (50:50)",
                    "volume": "10mL"
                }
            },
            {
                "name": "HPLC Analysis",
                "service_id": 1,
                "service_parameters": {
                    "method": "pharmaceutical_assay",
                    "injection_volume": "20µL"
                }
            }
        ]
        name = "Pharmaceutical Analysis Workflow"
    
    else:
        tasks = [
            {
                "name": "Sample Preparation",
                "service_id": 3,
                "service_parameters": {"method": "standard_prep"}
            },
            {
                "name": "Analysis",
                "service_id": 1,
                "service_parameters": {"method": "standard_analysis"}
            },
            {
                "name": "Data Processing",
                "service_parameters": {"output_format": "standard_report"}
            }
        ]
        name = "Standard Analysis Workflow"
    
    return {
        "name": name,
        "author": "AI Assistant",
        "tasks": tasks
    }

# Workflow control endpoints
@app.post("/api/workflows/{workflow_id}/pause")
def pause_workflow(workflow_id: int):
    workflow = next((w for w in workflows_db if w["id"] == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow["status"] == "running":
        workflow["status"] = "paused"
        workflow["updated_at"] = datetime.now().isoformat()
        return {"message": "Workflow paused successfully", "status": "paused"}
    else:
        raise HTTPException(status_code=400, detail=f"Cannot pause workflow with status: {workflow['status']}")

@app.post("/api/workflows/{workflow_id}/stop")
def stop_workflow(workflow_id: int):
    workflow = next((w for w in workflows_db if w["id"] == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow["status"] in ["running", "paused"]:
        workflow["status"] = "stopped"
        workflow["updated_at"] = datetime.now().isoformat()
        
        # Stop all running tasks
        for task in tasks_db:
            if task["workflow_id"] == workflow_id and task["status"] == "running":
                task["status"] = "stopped"
        
        return {"message": "Workflow stopped successfully", "status": "stopped"}
    else:
        raise HTTPException(status_code=400, detail=f"Cannot stop workflow with status: {workflow['status']}")

@app.post("/api/workflows/{workflow_id}/resume")
def resume_workflow(workflow_id: int):
    workflow = next((w for w in workflows_db if w["id"] == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow["status"] == "paused":
        workflow["status"] = "running"
        workflow["updated_at"] = datetime.now().isoformat()
        return {"message": "Workflow resumed successfully", "status": "running"}
    else:
        raise HTTPException(status_code=400, detail=f"Cannot resume workflow with status: {workflow['status']}")

@app.delete("/api/workflows/{workflow_id}")
def delete_workflow(workflow_id: int):
    global workflows_db, tasks_db
    
    workflow = next((w for w in workflows_db if w["id"] == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Remove workflow
    workflows_db = [w for w in workflows_db if w["id"] != workflow_id]
    
    # Remove associated tasks
    tasks_db = [t for t in tasks_db if t["workflow_id"] != workflow_id]
    
    return {"message": "Workflow deleted successfully"}

@app.get("/")
def root():
    return {"message": "Laboratory Automation Framework Demo API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)