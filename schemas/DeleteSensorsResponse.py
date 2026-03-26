from pydantic import BaseModel

class DeleteSensorsResponse(BaseModel):
    success: bool
    message: str
    deleted_count: int