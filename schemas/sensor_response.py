from datetime import datetime
from pydantic import Field
from .sensor import Sensor


class SensorResponse(Sensor):
    id: int
    timestamp: datetime | None = Field(default=None, description="UTC timestamp when sensor was recorded")
