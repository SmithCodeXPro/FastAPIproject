from pydantic import BaseModel
from .sensor_response import SensorResponse


class SensorMessageResponse(BaseModel):
    message: str
    sensor: SensorResponse
