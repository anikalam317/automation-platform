from pydantic import BaseModel, Field


class OperateCentrifuge(BaseModel):
    instrument_id: str
    rpm: int = Field(ge=0)
    duration: int = Field(ge=1)
