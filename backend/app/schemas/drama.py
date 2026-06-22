from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StylePresetUpdate(BaseModel):
    name: Optional[str] = None
    render_class: Optional[str] = None
    genre_tags: Optional[List[str]] = None
    style_description_md: Optional[str] = None
    narrative: Optional[Dict[str, Any]] = None
    visual: Optional[Dict[str, Any]] = None
    camera_defaults: Optional[Dict[str, Any]] = None
    model_prompts: Optional[Dict[str, str]] = None
    locked_tokens: Optional[List[str]] = None
    reference_images: Optional[List[Dict[str, Any]]] = None
    cover_url: Optional[str] = None
    cover_asset_id: Optional[str] = None
    status: Optional[str] = None


class StylePresetCreate(BaseModel):
    name: str
    render_class: str = "live_action"
    genre_tags: List[str] = Field(default_factory=list)
    style_id: Optional[str] = None
    style_description_md: Optional[str] = None
    model_prompts: Optional[Dict[str, str]] = None
    cover_url: Optional[str] = None
    cover_asset_id: Optional[str] = None
    reference_images: Optional[List[Dict[str, Any]]] = None
    publish: bool = Field(default=True, description="用户创建后是否立即可用")


class KnowledgeEntryCreate(BaseModel):
    entry_id: Optional[str] = None
    category: str
    domain: str = ""
    tags: List[str] = Field(default_factory=list)
    title: str
    summary: str = ""
    content_markdown: str = ""
    when_to_use: List[str] = Field(default_factory=list)
    when_to_avoid: List[str] = Field(default_factory=list)
    prompt_tokens_en: List[str] = Field(default_factory=list)
    status: str = "draft"


class KnowledgeEntryUpdate(BaseModel):
    category: Optional[str] = None
    domain: Optional[str] = None
    tags: Optional[List[str]] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    content_markdown: Optional[str] = None
    when_to_use: Optional[List[str]] = None
    when_to_avoid: Optional[List[str]] = None
    prompt_tokens_en: Optional[List[str]] = None
    status: Optional[str] = None


class KnowledgeImportRequest(BaseModel):
    source_type: str = Field(description="manual | file | feishu")
    category: str
    title: str = ""
    summary: str = ""
    content_markdown: str = ""
    tags: List[str] = Field(default_factory=list)
    feishu_url: Optional[str] = None
    filename: Optional[str] = None
    publish: bool = False


class FeishuPreviewRequest(BaseModel):
    url: str


class KnowledgeCategoryCreate(BaseModel):
    code: str = Field(min_length=2, max_length=48)
    name: str = Field(min_length=1, max_length=64)
    description: str = ""
    applicable_stages: List[str] = Field(default_factory=list)


class KnowledgeCategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    description: Optional[str] = None
    applicable_stages: Optional[List[str]] = None


class SkillCreate(BaseModel):
    skill_code: str
    name: str
    stage: str = "init"
    source: str = "online"
    source_type: str = Field(default="online", description="online | repo")
    repo_path: Optional[str] = None
    skill_content_md: str = ""
    system_markdown: str = ""
    user_markdown: str = ""
    script_files: List[str] = Field(default_factory=list)
    skill_meta: Dict[str, str] = Field(default_factory=dict)
    output_schema_id: str = ""
    required_memory: List[str] = Field(default_factory=list)
    default_knowledge_tags: List[str] = Field(default_factory=list)
    model_hint: Dict[str, Any] = Field(default_factory=dict)
    description: str = ""


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    stage: Optional[str] = None
    skill_content_md: Optional[str] = None
    system_markdown: Optional[str] = None
    user_markdown: Optional[str] = None
    script_files: Optional[List[str]] = None
    skill_meta: Optional[Dict[str, str]] = None
    output_schema_id: Optional[str] = None
    required_memory: Optional[List[str]] = None
    default_knowledge_tags: Optional[List[str]] = None
    model_hint: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    status: Optional[str] = None


class SkillImportRepoRequest(BaseModel):
    folder: str = Field(description="skills/ 下的子目录名")
    stage: str = "production"
    publish: bool = False
    target_skill_id: Optional[str] = Field(
        default=None,
        description="指定已有 Skill 文档 id 时走更新/重新导入，而非新建",
    )


class SkillReimportRepoRequest(BaseModel):
    folder: Optional[str] = Field(default=None, description="代码库子目录，默认用 Skill 已绑定的 repo_path")
    publish: bool = False


class SkillRollbackRequest(BaseModel):
    version_num: int = Field(ge=1, description="要回滚到的 version_num")


class DramaProjectCreate(BaseModel):
    title: str
    genre: str = ""
    target_platform: str = "竖屏短剧"
    episode_count: int = 20
    episode_duration_sec: int = 90
    style_preset_id: Optional[str] = None
    style_modifiers: List[str] = Field(default_factory=list)


class DramaProjectUpdate(BaseModel):
    title: Optional[str] = None
    stage: Optional[str] = None
    genre: Optional[str] = None
    target_platform: Optional[str] = None
    episode_count: Optional[int] = None
    episode_duration_sec: Optional[int] = None
    style_preset_id: Optional[str] = None
    style_modifiers: Optional[List[str]] = None


class DramaChatRequest(BaseModel):
    message: str
    stage: Optional[str] = None


class AgentThreadCreate(BaseModel):
    project_id: Optional[str] = None
    canvas_project_id: Optional[str] = None
    agent_mode: str = "creative_short_drama"
    model_code: Optional[str] = None
    style_preset_id: Optional[str] = None
    multi_episode: bool = False
    title: Optional[str] = None


class AgentThreadUpdate(BaseModel):
    stage: Optional[str] = None
    model_code: Optional[str] = None
    style_preset_id: Optional[str] = None
    agent_mode: Optional[str] = None
    multi_episode: Optional[bool] = None
    title: Optional[str] = None
    project_id: Optional[str] = None
    canvas_project_id: Optional[str] = None


class AgentRefItem(BaseModel):
    type: str = "asset"
    id: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None


class AgentChatRequest(BaseModel):
    message: str
    refs: List[AgentRefItem] = Field(default_factory=list)
    style_preset_id: Optional[str] = None


class KVSetRequest(BaseModel):
    namespace: str
    key: str
    value: Any
    ttl_seconds: Optional[int] = None
