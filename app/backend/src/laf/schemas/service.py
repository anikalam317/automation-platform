from pydantic import BaseModel
from typing import Optional, Dict, Any


class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str
    endpoint: str
    enabled: bool = True


class ServiceCreate(ServiceBase):
    default_parameters: Optional[Dict[str, Any]] = None


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    endpoint: Optional[str] = None
    default_parameters: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class ServiceResponse(ServiceBase):
    id: int
    default_parameters: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True