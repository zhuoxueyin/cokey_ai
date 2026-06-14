from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SessionCreate(BaseModel):
    category: str = Field(..., description="text/image/video")


class SessionResponse(BaseModel):
    id: str
    session_id: str
    category: str
    task_ids: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
