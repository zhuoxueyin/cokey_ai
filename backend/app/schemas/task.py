from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


TASK_STATUS_PENDING = "pending"
TASK_STATUS_QUEUED = "queued"
TASK_STATUS_PROCESSING = "processing"
TASK_STATUS_SUCCESS = "success"
TASK_STATUS_FAILED = "failed"
TASK_STATUS_CANCELLED = "cancelled"


class TaskBase(BaseModel):
    model_code: str
    category: str
    session_id: Optional[str] = None


class TaskCreate(TaskBase):
    params: Dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    id: str
    task_id: str
    session_id: Optional[str] = None
    model_code: str
    channel_code: Optional[str] = None
    category: str
    status: str
    params: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    trace_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskListItem(BaseModel):
    id: str
    task_id: str
    session_id: Optional[str]
    model_code: str
    channel_code: Optional[str]
    category: str
    status: str
    params_summary: str
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: datetime


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: datetime


class TaskQueryParams(BaseModel):
    session_id: Optional[str] = None
    model_code: Optional[str] = None
    channel_code: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
