from pydantic import BaseModel, Field, field_validator


class Sensor(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    temperature: float = Field(..., ge=-50, le=150)

    @field_validator("name")
    @classmethod
    def no_forbidden_names(cls, v: str) -> str:
        if v.lower() in {"test", "invalid"}:
            raise ValueError("This sensor name is not allowed")
        return v
