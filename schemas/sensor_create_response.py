from datetime import datetime
from pydantic import BaseModel


class SensorCreateResponse(BaseModel):
    message: str
    id: int
    name: str
    temperature: float
    timestamp: datetime
    alert: bool
