from pydantic import BaseModel, List


class OperateRobotArm(BaseModel):
    instrument_id: str
    movement_sequence: List[str]
