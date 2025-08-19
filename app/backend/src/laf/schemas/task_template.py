from pydantic import BaseModel
from typing import Optional, Dict, Any


class TaskTemplateBase(BaseModel):
    name: str
    description: str
    category: str
    type: str
    required_service_type: Optional[str] = None
    default_parameters: Dict[str, Any] = {}
    estimated_duration: int = 30  # minutes
    enabled: bool = True


class TaskTemplateCreate(TaskTemplateBase):
    pass


class TaskTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    required_service_type: Optional[str] = None
    default_parameters: Optional[Dict[str, Any]] = None
    estimated_duration: Optional[int] = None
    enabled: Optional[bool] = None


class TaskTemplateResponse(TaskTemplateBase):
    id: int

    class Config:
        from_attributes = True