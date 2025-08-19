from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...models.database import TaskTemplate
from ...schemas.task_template import TaskTemplateCreate, TaskTemplateResponse, TaskTemplateUpdate

router = APIRouter(prefix="/api/task-templates", tags=["task-templates"])


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