from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from .result import ResultResponse


class TaskBase(BaseModel):
    name: str
    order_index: int = 0


class TaskCreate(TaskBase):
    service_id: Optional[int] = None
    service_parameters: Optional[Dict[str, Any]] = None


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


class TaskResponse(TaskBase):
    id: int
    workflow_id: int
    service_id: Optional[int]
    service_parameters: Optional[Dict[str, Any]]
    status: str
    executed_at: datetime
    results: List[ResultResponse] = []
    manual_completion: Optional[bool] = None
    completed_by: Optional[str] = None
    completion_method: Optional[str] = None
    completion_timestamp: Optional[datetime] = None
    task_type: Optional[str] = None

    class Config:
        from_attributes = True
