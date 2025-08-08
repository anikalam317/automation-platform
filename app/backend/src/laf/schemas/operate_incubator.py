from pydantic import BaseModel, Field


class OperateIncubator(BaseModel):
    instrument_id: str
    temperature: float
    duration: int = Field(ge=1)
