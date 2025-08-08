from pydantic import BaseModel, List


class CalculatePotency(BaseModel):
    input_data: List[float]
