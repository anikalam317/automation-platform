from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from ...core.database import get_db
from ...models.database import TaskTemplate
from ...models.enhanced_models import TaskTemplateV2 as EnhancedTaskTemplate
from ...schemas.task_template import TaskTemplateCreate, TaskTemplateResponse, TaskTemplateUpdate
from ...schemas.enhanced_schemas import (
    TaskTemplateResponse as EnhancedTaskTemplateResponse, 
    TaskTemplateCreate as EnhancedTaskTemplateCreate,
    TaskTemplateUpdate as EnhancedTaskTemplateUpdate
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/task-templates", tags=["task-templates"])

# Enhanced router for new API version
enhanced_router = APIRouter(prefix="/api/v2/task-templates", tags=["Enhanced Task Templates"])


@router.post("/", response_model=TaskTemplateResponse, status_code=201)
def create_task_template(template: TaskTemplateCreate, db: Session = Depends(get_db)):
    db_template = TaskTemplate(
        name=template.name,
        description=template.description,
        category=template.category,
        type=template.type,
        required_service_type=template.required_service_type,
        default_parameters=template.default_parameters,
        estimated_duration=template.estimated_duration,
        enabled=template.enabled,
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


@router.get("/", response_model=List[TaskTemplateResponse])
def get_task_templates(db: Session = Depends(get_db)):
    templates = db.query(TaskTemplate).filter(TaskTemplate.enabled == True).all()
    return templates


@router.get("/{template_id}", response_model=TaskTemplateResponse)
def get_task_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(TaskTemplate).filter(TaskTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Task template not found")
    return template


@router.put("/{template_id}", response_model=TaskTemplateResponse)
def update_task_template(
    template_id: int, template_update: TaskTemplateUpdate, db: Session = Depends(get_db)
):
    template = db.query(TaskTemplate).filter(TaskTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Task template not found")

    if template_update.name is not None:
        template.name = template_update.name
    if template_update.description is not None:
        template.description = template_update.description
    if template_update.category is not None:
        template.category = template_update.category
    if template_update.type is not None:
        template.type = template_update.type
    if template_update.required_service_type is not None:
        template.required_service_type = template_update.required_service_type
    if template_update.default_parameters is not None:
        template.default_parameters = template_update.default_parameters
    if template_update.estimated_duration is not None:
        template.estimated_duration = template_update.estimated_duration
    if template_update.enabled is not None:
        template.enabled = template_update.enabled

    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}")
def delete_task_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(TaskTemplate).filter(TaskTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Task template not found")

    db.delete(template)
    db.commit()
    return {"message": "Task template deleted successfully"}


# Enhanced API endpoints for v2

@enhanced_router.get("/", response_model=List[EnhancedTaskTemplateResponse])
async def list_enhanced_task_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    capability: Optional[str] = Query(None, description="Filter by required capability"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    db: Session = Depends(get_db)
):
    """
    List all enhanced task templates with optional filtering
    
    **Filters:**
    - **category**: Template category (analytical, preparative, etc.)
    - **capability**: Required capability name
    - **tag**: Template tag
    """
    try:
        query = db.query(EnhancedTaskTemplate)
        
        if category:
            query = query.filter(EnhancedTaskTemplate.category == category)
        if capability:
            query = query.filter(EnhancedTaskTemplate.required_capabilities.op('@>')(f'["{capability}"]'))
        if tag:
            query = query.filter(EnhancedTaskTemplate.tags.op('@>')(f'["{tag}"]'))
        
        templates = query.all()
        
        logger.info(f"Retrieved {len(templates)} enhanced task templates")
        return templates
        
    except Exception as e:
        logger.error(f"Failed to list enhanced task templates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task templates: {str(e)}")

@enhanced_router.post("/", response_model=EnhancedTaskTemplateResponse)
async def create_enhanced_task_template(
    template_data: EnhancedTaskTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new enhanced task template
    
    **Template Creation:**
    - Defines reusable task configurations
    - Specifies capability requirements
    - Sets default parameters and validation schema
    - Provides duration estimates
    """
    try:
        # Check if template with same name already exists
        existing = db.query(EnhancedTaskTemplate).filter(EnhancedTaskTemplate.name == template_data.name).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Task template '{template_data.name}' already exists")
        
        template = EnhancedTaskTemplate(
            name=template_data.name,
            description=template_data.description,
            category=template_data.category,
            required_capabilities=template_data.required_capabilities,
            optional_capabilities=template_data.optional_capabilities,
            default_parameters=template_data.default_parameters,
            parameter_schema=template_data.parameter_schema,
            estimated_duration_seconds=template_data.estimated_duration_seconds,
            resource_requirements=template_data.resource_requirements,
            tags=template_data.tags
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        
        logger.info(f"Created enhanced task template: {template.name} (ID: {template.id})")
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create enhanced task template: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Template creation failed: {str(e)}")

@enhanced_router.get("/{template_id}", response_model=EnhancedTaskTemplateResponse)
async def get_enhanced_task_template(template_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific enhanced task template"""
    template = db.query(EnhancedTaskTemplate).filter(EnhancedTaskTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Task template not found")
    return template

@enhanced_router.get("/{template_id}/compatible-services")
async def get_compatible_services_for_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """Get services compatible with this task template"""
    try:
        template = db.query(EnhancedTaskTemplate).filter(EnhancedTaskTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Task template not found")
        
        from ...core.capability_matcher import CapabilityMatcher, TaskRequirements
        from ...models.enhanced_models import Service, ServiceStatus
        
        # Build requirements from template
        requirements = TaskRequirements(
            task_type=template.name,
            required_capabilities=template.required_capabilities or [],
            optional_capabilities=template.optional_capabilities or [],
            resource_requirements=template.resource_requirements or {}
        )
        
        # Get all available services
        services = db.query(Service).filter(Service.status == ServiceStatus.ONLINE).all()
        
        # Find compatible services
        matcher = CapabilityMatcher(db)
        match_scores = matcher.match_capabilities(requirements, services)
        
        # Filter for adequate or better matches
        compatible_matches = [
            score for score in match_scores 
            if score.quality.value not in ['poor', 'incompatible']
        ]
        
        return {
            "template_id": template_id,
            "template_name": template.name,
            "total_services_checked": len(services),
            "compatible_services_count": len(compatible_matches),
            "compatible_services": [
                {
                    "service_id": match.service_id,
                    "service_name": match.service_name,
                    "match_quality": match.quality.value,
                    "match_score": match.score,
                    "confidence": match.confidence,
                    "reasons": match.reasons
                }
                for match in compatible_matches
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get compatible services for template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Compatibility check failed: {str(e)}")

@enhanced_router.post("/{template_id}/validate-parameters")
async def validate_template_parameters(
    template_id: int,
    parameters: dict,
    db: Session = Depends(get_db)
):
    """Validate parameters against template schema"""
    try:
        template = db.query(EnhancedTaskTemplate).filter(EnhancedTaskTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Task template not found")
        
        validation_errors = []
        warnings = []
        
        # Basic validation against parameter schema
        if template.parameter_schema:
            schema = template.parameter_schema
            
            # Check required parameters
            required_params = schema.get('required', [])
            for param in required_params:
                if param not in parameters:
                    validation_errors.append(f"Missing required parameter: {param}")
            
            # Check parameter types and constraints
            properties = schema.get('properties', {})
            for param, value in parameters.items():
                if param in properties:
                    param_schema = properties[param]
                    
                    # Type validation
                    expected_type = param_schema.get('type')
                    if expected_type:
                        if expected_type == 'number' and not isinstance(value, (int, float)):
                            validation_errors.append(f"Parameter '{param}' must be a number")
                        elif expected_type == 'string' and not isinstance(value, str):
                            validation_errors.append(f"Parameter '{param}' must be a string")
                        elif expected_type == 'boolean' and not isinstance(value, bool):
                            validation_errors.append(f"Parameter '{param}' must be boolean")
                    
                    # Range validation
                    if 'minimum' in param_schema and isinstance(value, (int, float)):
                        if value < param_schema['minimum']:
                            validation_errors.append(f"Parameter '{param}' below minimum: {value} < {param_schema['minimum']}")
                    
                    if 'maximum' in param_schema and isinstance(value, (int, float)):
                        if value > param_schema['maximum']:
                            validation_errors.append(f"Parameter '{param}' above maximum: {value} > {param_schema['maximum']}")
                else:
                    warnings.append(f"Parameter '{param}' not defined in template schema")
        
        is_valid = len(validation_errors) == 0
        
        return {
            "template_id": template_id,
            "template_name": template.name,
            "is_valid": is_valid,
            "validation_errors": validation_errors,
            "warnings": warnings,
            "validated_parameters": parameters
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Parameter validation failed for template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Parameter validation failed: {str(e)}")