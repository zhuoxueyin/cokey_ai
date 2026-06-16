from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


CHANNEL_TYPE_AGGREGATOR = "aggregator"
CHANNEL_TYPE_DIRECT = "direct"

CHANNEL_STATUS_ACTIVE = "active"
CHANNEL_STATUS_INACTIVE = "inactive"


class ChannelAuthConfig(BaseModel):
    api_key: Optional[str] = None


class ChannelApiConfig(BaseModel):
    """渠道 API 路径配置"""
    text_path: str = "/chat/completions"
    image_path: str = "/images/generations"
    video_path: str = "/videos/generations"
    text_stream: bool = True


class ChannelRetryConfig(BaseModel):
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 2


class ChannelRateLimitConfig(BaseModel):
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000


class ChannelBase(BaseModel):
    channel_code: str = Field(..., min_length=2, max_length=50)
    channel_name: str = Field(..., min_length=1, max_length=100)
    channel_type: str = Field(..., description="aggregator/direct")
    base_url: str = Field(..., description="接口根地址")
    auth_config: ChannelAuthConfig
    api_config: ChannelApiConfig = Field(default_factory=ChannelApiConfig)
    retry_config: ChannelRetryConfig = Field(default_factory=ChannelRetryConfig)
    rate_limit_config: ChannelRateLimitConfig = Field(default_factory=ChannelRateLimitConfig)
    status: str = Field(default=CHANNEL_STATUS_ACTIVE)
    description: Optional[str] = None


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(BaseModel):
    channel_name: Optional[str] = None
    channel_type: Optional[str] = None
    base_url: Optional[str] = None
    auth_config: Optional[ChannelAuthConfig] = None
    api_config: Optional[ChannelApiConfig] = None
    retry_config: Optional[ChannelRetryConfig] = None
    rate_limit_config: Optional[ChannelRateLimitConfig] = None
    status: Optional[str] = None
    description: Optional[str] = None


class ChannelResponse(BaseModel):
    id: str
    channel_code: str
    channel_name: str
    channel_type: str
    base_url: str
    auth_config: ChannelAuthConfig
    api_config: ChannelApiConfig
    retry_config: ChannelRetryConfig
    rate_limit_config: ChannelRateLimitConfig
    status: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChannelListItem(BaseModel):
    id: str
    channel_code: str
    channel_name: str
    channel_type: str
    status: str
    description: Optional[str] = None
    created_at: datetime
