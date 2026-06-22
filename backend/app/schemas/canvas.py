from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


CanvasNodeType = Literal["resource", "text", "image", "video", "group", "title"]
CanvasNodeStatus = Literal["idle", "running", "success", "failed"]


class CanvasViewport(BaseModel):
    x: float = 0
    y: float = 0
    zoom: float = 1


class CanvasProjectCreate(BaseModel):
    title: str = Field(default="未命名项目", max_length=120)
    user_id: Optional[str] = None


class CanvasProjectUpdate(BaseModel):
    title: Optional[str] = None
    viewport: Optional[CanvasViewport] = None
    user_id: Optional[str] = None


class CanvasNodePosition(BaseModel):
    x: float = 0
    y: float = 0


class CanvasNodeConfig(BaseModel):
    prompt: str = ""
    model_code: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    resource_url: Optional[str] = None
    resource_type: Optional[Literal["image", "video"]] = None
    resource_name: Optional[str] = None
    text_mode: Optional[Literal["manual", "generate"]] = None
    content: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    user_resized: Optional[bool] = None
    output_image_index: Optional[int] = None
    style_preset_id: Optional[str] = None
    style_preset_name: Optional[str] = None


class CanvasNodeCreate(BaseModel):
    node_type: CanvasNodeType
    title: Optional[str] = None
    position: CanvasNodePosition = Field(default_factory=CanvasNodePosition)
    config: CanvasNodeConfig = Field(default_factory=CanvasNodeConfig)
    parent_id: Optional[str] = None


class CanvasNodeUpdate(BaseModel):
    title: Optional[str] = None
    position: Optional[CanvasNodePosition] = None
    config: Optional[CanvasNodeConfig] = None
    status: Optional[CanvasNodeStatus] = None
    input_stale: Optional[bool] = None
    result: Optional[Dict[str, Any]] = None
    task_id: Optional[str] = None
    error_message: Optional[str] = None
    result_version: Optional[int] = None
    upstream_snapshot: Optional[Dict[str, Any]] = None
    parent_id: Optional[str] = None


class CanvasEdgeCreate(BaseModel):
    source_node_id: str
    target_node_id: str
    source_handle: str = "output"
    target_handle: str = "input"


class CanvasBatchSync(BaseModel):
    viewport: Optional[CanvasViewport] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None


class CanvasNodeRun(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    config_override: Optional[CanvasNodeConfig] = None


class CanvasNodeDuplicate(BaseModel):
    position: Optional[CanvasNodePosition] = None
