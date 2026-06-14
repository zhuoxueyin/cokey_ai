from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


FIELD_TYPE_TEXT = "text"
FIELD_TYPE_TEXTAREA = "textarea"
FIELD_TYPE_NUMBER = "number"
FIELD_TYPE_SLIDER = "slider"
FIELD_TYPE_SELECT = "select"
FIELD_TYPE_SWITCH = "switch"
FIELD_TYPE_IMAGE_UPLOAD = "image_upload"


CATEGORY_TEXT = "text"
CATEGORY_IMAGE = "image"
CATEGORY_VIDEO = "video"

MODEL_STATUS_ONLINE = "online"
MODEL_STATUS_OFFLINE = "offline"
MODEL_STATUS_MAINTENANCE = "maintenance"


class ParamSchemaField(BaseModel):
    name: str = Field(..., description="参数名")
    label: str = Field(..., description="显示名称")
    field_type: str = Field(..., description="控件类型:text/textarea/number/slider/select/switch/image_upload")
    required: bool = False
    default: Optional[Any] = None
    placeholder: Optional[str] = None
    options: Optional[List[Dict[str, Any]]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    help_text: Optional[str] = None
    show_when: Optional[Dict[str, Any]] = None


class ParamSchema(BaseModel):
    fields: List[ParamSchemaField] = Field(default_factory=list)


class ChannelBinding(BaseModel):
    channel_code: str
    channel_model_id: str
    priority: int = 1
    status: str = "active"


class ModelBase(BaseModel):
    model_code: str = Field(..., min_length=2, max_length=50)
    model_name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., description="text/image/video")
    cover: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    channel_bindings: List[ChannelBinding] = Field(default_factory=list)
    param_schema: ParamSchema = Field(default_factory=ParamSchema)
    status: str = Field(default=MODEL_STATUS_ONLINE)
    sort_order: int = 0
    is_default: bool = False


class ModelCreate(ModelBase):
    pass


class ModelUpdate(BaseModel):
    model_name: Optional[str] = None
    category: Optional[str] = None
    cover: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    channel_bindings: Optional[List[ChannelBinding]] = None
    param_schema: Optional[ParamSchema] = None
    status: Optional[str] = None
    sort_order: Optional[int] = None
    is_default: Optional[bool] = None


class ModelResponse(BaseModel):
    id: str
    model_code: str
    model_name: str
    category: str
    cover: Optional[str] = None
    description: Optional[str] = None
    tags: List[str]
    channel_bindings: List[ChannelBinding]
    param_schema: ParamSchema
    status: str
    sort_order: int
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelListItem(BaseModel):
    id: str
    model_code: str
    model_name: str
    category: str
    cover: Optional[str] = None
    description: Optional[str] = None
    tags: List[str]
    status: str
    sort_order: int
    is_default: bool
    created_at: datetime


class ModelPublicItem(BaseModel):
    id: str
    model_code: str
    model_name: str
    category: str
    cover: Optional[str] = None
    description: Optional[str] = None
    tags: List[str]
    is_default: bool
