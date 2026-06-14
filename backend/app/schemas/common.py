from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class UploadResponse(BaseModel):
    url: str
    file_path: str
    file_size: int
    content_type: str


class BatchImportRequest(BaseModel):
    channel_code: str


class BatchImportResult(BaseModel):
    total: int
    imported: int
    skipped: int
    failed: int
    messages: List[str] = Field(default_factory=list)
