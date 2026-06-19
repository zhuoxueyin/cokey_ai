from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# 主类型：聚合/直连
CHANNEL_TYPE_AGGREGATOR = "aggregator"
CHANNEL_TYPE_DIRECT = "direct"

# 聚合渠道具体枚举
CHANNEL_PROVIDER_WEELINKING = "weelinking"
CHANNEL_PROVIDER_APIYI = "apiyi"

# 直连渠道具体枚举
CHANNEL_PROVIDER_VOLCENGINE = "volcengine"

# 全部具体渠道枚举
ALL_CHANNEL_PROVIDERS = [
    CHANNEL_PROVIDER_WEELINKING,
    CHANNEL_PROVIDER_APIYI,
    CHANNEL_PROVIDER_VOLCENGINE,
]

# 具体渠道 -> 主类型 映射
CHANNEL_PROVIDER_TO_MAIN_TYPE: Dict[str, str] = {
    CHANNEL_PROVIDER_WEELINKING: CHANNEL_TYPE_AGGREGATOR,
    CHANNEL_PROVIDER_APIYI: CHANNEL_TYPE_AGGREGATOR,
    CHANNEL_PROVIDER_VOLCENGINE: CHANNEL_TYPE_DIRECT,
}

# 具体渠道 -> 中文名称
CHANNEL_PROVIDER_LABELS: Dict[str, str] = {
    CHANNEL_PROVIDER_WEELINKING: "微链 WeeLinking",
    CHANNEL_PROVIDER_APIYI: "APIYi",
    CHANNEL_PROVIDER_VOLCENGINE: "火山引擎",
}

CHANNEL_STATUS_ACTIVE = "active"
CHANNEL_STATUS_INACTIVE = "inactive"


class ChannelAuthConfig(BaseModel):
    api_key: Optional[str] = None


class ChannelApiConfig(BaseModel):
    """渠道 API 路径配置"""
    text_path: str = "/chat/completions"
    image_path: str = "/images/generations"
    image_edits_path: Optional[str] = "/images/edits"
    video_path: str = "/videos/generations"
    video_image_path: Optional[str] = None
    audio_path: Optional[str] = None
    text_stream: bool = True


class ChannelRetryConfig(BaseModel):
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 2

    @model_validator(mode="before")
    @classmethod
    def fill_int_defaults(cls, data: Any) -> Any:
        if isinstance(data, dict):
            defaults = {"timeout": 30, "max_retries": 3, "retry_delay": 2}
            for key, default in defaults.items():
                if data.get(key) is None or data.get(key) == "":
                    data[key] = default
        return data


class ChannelRateLimitConfig(BaseModel):
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000

    @model_validator(mode="before")
    @classmethod
    def fill_int_defaults(cls, data: Any) -> Any:
        if isinstance(data, dict):
            defaults = {
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "requests_per_day": 10000,
            }
            for key, default in defaults.items():
                if data.get(key) is None or data.get(key) == "":
                    data[key] = default
        return data


class ParamMapping(BaseModel):
    """参数映射规则（兼容旧格式）"""
    source: str = Field(..., description="源参数名，支持多级：images.0.url")
    target: str = Field(..., description="目标字段名，支持多级：inputs.image")
    default: Optional[Any] = Field(default=None, description="默认值")
    transform: Optional[str] = Field(default=None, description="转换规则: first_image/cdn_url/int/float/str/json")


class ResponseMapping(BaseModel):
    """响应映射规则（兼容旧格式，响应由系统自动完成，无需手动配置）"""
    source: str = Field(..., description="源字段路径，如: data.0.url")
    target: str = Field(..., description="目标字段，如: images.0.url")
    content_type: str = Field(default="text", description="内容类型: text/image/video/audio")


class BodyParam(BaseModel):
    """Body 入参定义

    新格式（推荐）— 取值来源与配置分离：
      - source=literal      → literal 填固定字面量（可 JSON）
      - source=task_param   → param 填任务参数字段名（留空=与 key 同名）
      - source=builtin      → builtin 填 channel_model_id / channel_code / trace_id
      - source=image_urls   → param 填图片列表字段名（默认 images）
      - source=chat_messages → 由 prompt + images 自动组装 OpenAI messages

    旧格式（兼容）：value_type + value
    """
    key: str = Field(..., description="请求体字段名")
    source: Optional[str] = Field(
        default=None,
        description="literal | task_param | builtin | image_urls | chat_messages",
    )
    literal: Optional[str] = Field(default=None, description="source=literal 时的固定值")
    param: Optional[str] = Field(default=None, description="source=task_param/image_urls 时的源字段名")
    builtin: Optional[str] = Field(default=None, description="source=builtin 时的内置变量名")
    value_type: Optional[str] = Field(default=None, description="[兼容] fixed / dynamic / image")
    value: Optional[str] = Field(default="", description="[兼容] 旧版取值配置")
    description: Optional[str] = Field(default=None, description="参数说明")


class EndpointConfig(BaseModel):
    """端点配置

    新配置方式（推荐）：
      - content_type: Content-Type，默认 application/json
      - headers: 自定义 headers（不含 Authorization，Authorization 由系统自动加 Bearer {api_key}）
      - body_params: Body 入参表（key + value_type + value），由系统自动构建请求体
      - 响应：无需配置，由适配器自动识别并提取

    旧配置方式（保持兼容）：params_template / param_mappings / required_params / default_params /
      response_mappings / response_extract_path
    """
    type: str = Field(..., description="端点类型(兼容): text/image/image_edits/video/video_image/audio/chat/other")
    protocol_slot: Optional[str] = Field(
        default=None,
        description="协议槽位(推荐): openai.chat.completions / openai.images.generations / ...",
    )
    endpoint: str = Field(..., description="端点路径，如: chat/completions")
    method: str = Field(default="POST", description="HTTP方法: POST/GET/PUT/DELETE")
    description: Optional[str] = None

    # —— 新配置方式（推荐）——
    content_type: Optional[str] = Field(default="application/json", description="Content-Type，默认 application/json")
    headers: Optional[Dict[str, str]] = Field(default=None, description="自定义 headers，Authorization 由系统自动处理")
    body_params: Optional[List[BodyParam]] = Field(default=None, description="Body 入参表（优先于 params_template）")

    # —— 旧配置方式（保持兼容）——
    params_template: Optional[Dict[str, Any]] = Field(default=None, description="请求体参数模板，支持 {prompt}/{model} 占位符")
    param_mappings: Optional[List[ParamMapping]] = Field(default=None, description="参数映射规则列表")
    required_params: Optional[List[str]] = Field(default=None, description="必填参数列表")
    default_params: Optional[Dict[str, Any]] = Field(default=None, description="默认参数值")

    response_mappings: Optional[List[ResponseMapping]] = Field(default=None, description="响应映射规则（系统自动识别）")
    response_extract_path: Optional[str] = Field(default=None, description="响应内容提取路径（系统自动识别）")

    @model_validator(mode="before")
    @classmethod
    def clean_legacy_mappings(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        for key in ("param_mappings", "response_mappings"):
            items = data.get(key)
            if isinstance(items, list):
                data[key] = [
                    item for item in items
                    if isinstance(item, dict) and item.get("source") and item.get("target")
                ] or None
        return data


class ChannelBase(BaseModel):
    channel_code: str = Field(..., min_length=2, max_length=50)
    channel_name: str = Field(..., min_length=1, max_length=100)
    channel_type: str = Field(..., description="主类型: aggregator(聚合) / direct(直连)")
    channel_provider: Optional[str] = Field(default=None, description="具体渠道枚举: weelinking / apiyi / volcengine")
    base_url: str = Field(..., description="接口根地址")
    auth_config: ChannelAuthConfig
    api_config: ChannelApiConfig = Field(default_factory=ChannelApiConfig)
    endpoints: List[EndpointConfig] = Field(default_factory=list)
    retry_config: ChannelRetryConfig = Field(default_factory=ChannelRetryConfig)
    rate_limit_config: ChannelRateLimitConfig = Field(default_factory=ChannelRateLimitConfig)
    status: str = Field(default=CHANNEL_STATUS_ACTIVE)
    description: Optional[str] = None

    @field_validator("channel_type")
    @classmethod
    def validate_channel_type(cls, v: str) -> str:
        allowed = {CHANNEL_TYPE_AGGREGATOR, CHANNEL_TYPE_DIRECT}
        if v not in allowed:
            raise ValueError(f"channel_type 必须是 {allowed} 之一")
        return v

    @field_validator("channel_provider")
    @classmethod
    def validate_channel_provider(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if v not in ALL_CHANNEL_PROVIDERS:
            raise ValueError(f"channel_provider 必须是 {ALL_CHANNEL_PROVIDERS} 之一")
        return v

    @model_validator(mode="before")
    @classmethod
    def infer_channel_type(cls, data: Any) -> Any:
        """channel_type 未传时根据 channel_provider 推断"""
        if not isinstance(data, dict):
            return data
        if not data.get("channel_type") and data.get("channel_provider"):
            data["channel_type"] = CHANNEL_PROVIDER_TO_MAIN_TYPE.get(
                data["channel_provider"], CHANNEL_TYPE_AGGREGATOR
            )
        return data


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(BaseModel):
    channel_name: Optional[str] = None
    channel_type: Optional[str] = None
    channel_provider: Optional[str] = None
    base_url: Optional[str] = None
    auth_config: Optional[ChannelAuthConfig] = None
    api_config: Optional[ChannelApiConfig] = None
    endpoints: Optional[List[EndpointConfig]] = None
    retry_config: Optional[ChannelRetryConfig] = None
    rate_limit_config: Optional[ChannelRateLimitConfig] = None
    status: Optional[str] = None
    description: Optional[str] = None


class ChannelResponse(BaseModel):
    id: str
    channel_code: str
    channel_name: str
    channel_type: str
    channel_provider: Optional[str] = None
    base_url: str
    auth_config: ChannelAuthConfig
    api_config: ChannelApiConfig
    endpoints: List[EndpointConfig] = Field(default_factory=list)
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
