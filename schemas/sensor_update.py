from pydantic import BaseModel, Field


class SensorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    temperature: float | None = Field(default=None, ge=-50, le=150)
