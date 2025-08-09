from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, Dict, Any


class BioviaExperimentTask(BaseModel):
    external_system: str = "Biovia Onelab"
    external_task_id: str
    external_resource_url: Optional[HttpUrl]
    external_method: Optional[str] = None
    external_version: Optional[str] = None
    external_metadata: Optional[Dict[str, Any]] = None
    executed_by: Optional[EmailStr] = None
    parameters: Dict[str, Any]
    kubernetes_image: str
    kubernetes_command: Optional[List[str]] = None
    kubernetes_env: Optional[Dict[str, str]] = None

    class Config:
        # Allow extra fields not defined in the model
        extra = "allow"
        # Provide example for OpenAPI/JSON Schema docs
        schema_extra = {
            "example": {
                "external_system": "Biovia Onelab",
                "external_task_id": "EXP-12345",
                "external_resource_url": "https://biovia.example.com/api/experiments/EXP-12345",
                "kubernetes_image": "biovia/experiment-runner:latest",
            }
        }
        # Enable ORM mode for compatibility with SQLAlchemy models
        orm_mode = True
        # Example of field aliasing
        fields = {
            "external_task_id": {"alias": "eln_id"},
            "external_resource_url": {"alias": "eln_url"},
        }
