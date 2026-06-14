from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class StatsQueryParams(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    category: Optional[str] = None


class ModelStats(BaseModel):
    model_code: str
    model_name: str
    total_count: int
    success_count: int
    failed_count: int
    success_rate: float
    avg_duration_ms: float


class ChannelStats(BaseModel):
    channel_code: str
    channel_name: str
    total_count: int
    success_count: int
    failed_count: int
    success_rate: float
    avg_duration_ms: float


class OverallStats(BaseModel):
    total_tasks: int
    success_count: int
    failed_count: int
    success_rate: float
    avg_duration_ms: float
    model_stats: List[ModelStats]
    channel_stats: List[ChannelStats]
