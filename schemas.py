from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class Sensor(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    temperature: float = Field(..., ge=-50, le=150)

    @field_validator("name")
    @classmethod
    def no_forbidden_names(cls, v: str) -> str:
        if v.lower() in {"test", "invalid"}:
            raise ValueError("This sensor name is not allowed")
        return v


class SensorResponse(Sensor):
    id: int
    timestamp: datetime | None = Field(default=None, description="UTC timestamp when sensor was recorded")


class SensorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    temperature: float | None = Field(default=None, ge=-50, le=150)


class SensorCreateResponse(BaseModel):
    message: str
    id: int
    name: str
    temperature: float
    timestamp: datetime
    alert: bool


class SensorMessageResponse(BaseModel):
    message: str
    sensor: SensorResponse
