from pydantic import BaseModel, EmailStr


class TransportSample(BaseModel):
    scientist: EmailStr
    task_id: int
    sample_id: int
    from_location: str
    to_location: str
    timestamp: Optional[str] = None  # ISO 8601 format
    priority: Optional[str] = None  # e.g., 'low', 'normal', 'high'
    notes: Optional[str] = None
