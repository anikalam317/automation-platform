from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json

router = APIRouter(prefix="/api/ai", tags=["ai"])


class WorkflowGenerationRequest(BaseModel):
    prompt: str


class GeneratedTask(BaseModel):
    name: str
    service_id: Optional[int] = None
    service_parameters: Optional[Dict[str, Any]] = None


class GeneratedWorkflow(BaseModel):
    name: str
    author: str
    tasks: List[GeneratedTask]


@router.post("/generate-workflow", response_model=GeneratedWorkflow)
async def generate_workflow(request: WorkflowGenerationRequest):
    """
    Generate a workflow from a natural language prompt.
    This is a simplified implementation that uses pattern matching.
    In production, this would integrate with an LLM service.
    """
    
    prompt = request.prompt.lower()
    
    # Simple pattern matching for demo purposes
    # In production, this would use a proper LLM integration
    
    workflow_name = "AI Generated Workflow"
    tasks = []
    
    # Analyze prompt for common laboratory operations
    if "hplc" in prompt or "chromatography" in prompt:
        if "prep" in prompt or "preparation" in prompt:
            tasks.append(GeneratedTask(
                name="Sample Preparation",
                service_parameters={
                    "dilution_factor": 10,
                    "solvent": "methanol",
                    "volume": "1mL"
                }
            ))
        
        tasks.append(GeneratedTask(
            name="HPLC Analysis",
            service_parameters={
                "method": "gradient_method_1",
                "injection_volume": "10µL",
                "column_temp": "30°C",
                "flow_rate": "1.0mL/min"
            }
        ))
        
        workflow_name = "HPLC Analysis Workflow"
    
    elif "gc-ms" in prompt or "gas chromatography" in prompt:
        if "prep" in prompt or "preparation" in prompt:
            tasks.append(GeneratedTask(
                name="Sample Preparation",
                service_parameters={
                    "extraction_method": "liquid-liquid",
                    "solvent": "hexane",
                    "volume": "2mL"
                }
            ))
        
        tasks.append(GeneratedTask(
            name="GC-MS Analysis",
            service_parameters={
                "method": "volatiles_screening",
                "injection_mode": "splitless",
                "oven_program": "40°C-300°C",
                "scan_range": "50-500 m/z"
            }
        ))
        
        workflow_name = "GC-MS Analysis Workflow"
    
    elif "pharmaceutical" in prompt or "drug" in prompt:
        tasks.extend([
            GeneratedTask(
                name="Sample Weighing",
                service_parameters={
                    "target_weight": "100mg",
                    "tolerance": "±1mg"
                }
            ),
            GeneratedTask(
                name="Sample Dissolution",
                service_parameters={
                    "solvent": "methanol/water (50:50)",
                    "volume": "10mL",
                    "mixing_time": "15min"
                }
            ),
            GeneratedTask(
                name="HPLC Analysis",
                service_parameters={
                    "method": "pharmaceutical_assay",
                    "injection_volume": "20µL",
                    "run_time": "30min"
                }
            ),
            GeneratedTask(
                name="Data Analysis",
                service_parameters={
                    "analysis_type": "quantitative",
                    "standard_curve": "external",
                    "report_format": "USP"
                }
            )
        ])
        
        workflow_name = "Pharmaceutical Analysis Workflow"
    
    elif "environmental" in prompt or "water" in prompt or "soil" in prompt:
        tasks.extend([
            GeneratedTask(
                name="Sample Extraction",
                service_parameters={
                    "extraction_method": "solid_phase",
                    "cartridge": "C18",
                    "elution_solvent": "methanol"
                }
            ),
            GeneratedTask(
                name="GC-MS Screening",
                service_parameters={
                    "method": "environmental_screening",
                    "injection_mode": "splitless",
                    "scan_mode": "full_scan"
                }
            ),
            GeneratedTask(
                name="Data Processing",
                service_parameters={
                    "library_search": "NIST",
                    "reporting_limit": "µg/L",
                    "quality_control": "EPA_method"
                }
            )
        ])
        
        workflow_name = "Environmental Analysis Workflow"
    
    elif "protein" in prompt or "purification" in prompt:
        tasks.extend([
            GeneratedTask(
                name="Cell Lysis",
                service_parameters={
                    "buffer": "lysis_buffer",
                    "incubation_time": "30min",
                    "temperature": "4°C"
                }
            ),
            GeneratedTask(
                name="Chromatographic Purification",
                service_parameters={
                    "column_type": "ion_exchange",
                    "buffer_A": "20mM Tris pH 8.0",
                    "buffer_B": "20mM Tris + 1M NaCl pH 8.0",
                    "gradient": "linear"
                }
            ),
            GeneratedTask(
                name="Protein Analysis",
                service_parameters={
                    "method": "SDS-PAGE",
                    "gel_percentage": "12%",
                    "staining": "coomassie"
                }
            )
        ])
        
        workflow_name = "Protein Purification Workflow"
    
    else:
        # Default workflow for unrecognized prompts
        tasks.extend([
            GeneratedTask(
                name="Sample Preparation",
                service_parameters={
                    "method": "standard_prep",
                    "volume": "1mL"
                }
            ),
            GeneratedTask(
                name="Analysis",
                service_parameters={
                    "method": "standard_analysis"
                }
            ),
            GeneratedTask(
                name="Data Processing",
                service_parameters={
                    "output_format": "standard_report"
                }
            )
        ])
        
        workflow_name = "Standard Analysis Workflow"
    
    # Always add data processing if not already included
    if not any("data" in task.name.lower() or "processing" in task.name.lower() for task in tasks):
        tasks.append(GeneratedTask(
            name="Data Processing and Reporting",
            service_parameters={
                "report_format": "PDF",
                "include_statistics": True,
                "archive_data": True
            }
        ))
    
    return GeneratedWorkflow(
        name=workflow_name,
        author="AI Assistant",
        tasks=tasks
    )