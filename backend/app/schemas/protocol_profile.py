from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.schemas.channel import BodyParam


class ProtocolHttpConfig(BaseModel):
    path: str = Field(..., description="相对 base_url 的路径，如 images/generations")
    method: str = Field(default="POST")
    content_type: str = Field(default="application/json")


class ProtocolRequestConfig(BaseModel):
    """请求构建配置：builder 优先，否则走 config_engine body_params。"""
    builder: Optional[str] = Field(
        default=None,
        description="内置构建器: apiyi_chat_image / apiyi_vip_generations / config_engine / weelink_default",
    )
    body_params: Optional[List[BodyParam]] = None
    forbidden_fields: List[str] = Field(default_factory=list)
    size_strategy: Optional[str] = Field(
        default=None,
        description="api_field | prompt_hint | none",
    )
    extra: Dict[str, Any] = Field(default_factory=dict)


class ProtocolResponseConfig(BaseModel):
    parser: Optional[str] = Field(
        default=None,
        description="openai_images | markdown_image | config_engine | weelink_default",
    )
    extract_path: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class ProtocolProfileBase(BaseModel):
    profile_id: str = Field(..., min_length=2, max_length=120, description="唯一 ID，如 apiyi.gpt-image-2-vip.text_to_image")
    name: str = Field(..., min_length=1, max_length=200)
    provider: Optional[str] = Field(default=None, description="apiyi / weelinking / volcengine / *")
    protocol_slot: str = Field(..., description="协议槽位，如 openai.images.generations")
    invocation_mode: str = Field(..., description="text_chat / text_to_image / image_to_image / ...")
    endpoint_type: str = Field(..., description="渠道 endpoints[].type 兼容键: chat/image/image_edits/...")
    http: ProtocolHttpConfig
    request: ProtocolRequestConfig = Field(default_factory=ProtocolRequestConfig)
    response: ProtocolResponseConfig = Field(default_factory=ProtocolResponseConfig)
    description: Optional[str] = None
    status: str = Field(default="active")
    is_builtin: bool = Field(default=False, description="内置画像不可删除，可被 DB 覆盖")


class ProtocolProfileCreate(ProtocolProfileBase):
    pass


class ProtocolProfileUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    protocol_slot: Optional[str] = None
    invocation_mode: Optional[str] = None
    endpoint_type: Optional[str] = None
    http: Optional[ProtocolHttpConfig] = None
    request: Optional[ProtocolRequestConfig] = None
    response: Optional[ProtocolResponseConfig] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ProtocolProfileResponse(ProtocolProfileBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
