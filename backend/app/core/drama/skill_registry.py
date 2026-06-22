"""创作助手 Skill 注册表：运行时仅允许使用 Skill 库（MongoDB）已发布 Skill。"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

# 阶段 → Skill Code（须在 Skill 库注册并发布后才可被创作助手加载）
STAGE_SKILL_MAP: Dict[str, str] = {
    "init": "skill.intake",
    "concept": "skill.concept",
    "outline": "skill.concept",
    "script": "skill.script",
    "character": "skill.character",
    "scene": "skill.scene",
    "storyboard": "skill.storyboard",
    "production": "skill.production",
    "prompt_pack": "skill.prompt_engineer",
}

STAGES_WITHOUT_SKILL: frozenset[str] = frozenset()

PRODUCTION_SKILL_SKIP_SUMMARY = "生产阶段 · 无限画布"
PRODUCTION_SKILL_SKIP_DETAIL = "本阶段在无限画布完成出图/出视频，不绑定创作 Skill。"

PRODUCTION_OUTPUT_OVERRIDE = """【运行约束 · 覆盖旧版输出要求 · 反拖沓】
生产阶段须严格按子步骤路由（P0 盘点 / P1 章节规划 / P2 单格生产包 / P3 章确认），**每轮只做一个子步骤**。
禁止每轮重复生产路径说明、禁止同质化开场、禁止无请求重贴全表。
P2 单格交付须含：格位摘要 + `image-prompt` + `video-prompt` + `production-tasks`（prod_image + prod_video）。
对客以中文 Markdown 为主；prompt 块英文；JSON 仅用于 production-tasks。
若 Skill 正文与以上冲突，以本条为准。"""

CONCEPT_OUTPUT_OVERRIDE = """【运行约束 · 覆盖旧版输出要求】
创意脑暴须按对话进度执行单个子步骤（3A 风格包 / 3B 深化 / 3C 定稿+大纲），禁止多轮重复比选。
对客仅输出中文 Markdown，禁止 JSON/YAML/代码块。
用户选定 A/B/C 后不得再列另外两个方向；定稿后输出 `## 定稿方向` + `## 剧本大纲` 并引导进入 outline。
若 Skill 正文与以上冲突，以本条为准。"""

SKILL_NOT_REGISTERED_MSG = (
    "尚未在 Skill 库注册发布。请先在「Skill 库」在线新建或从代码库导入并发布，"
    "创作助手不会直接读取 skills/ 目录。"
)


class SkillNotRegisteredError(ValueError):
    """Skill 未在 Skill 库注册发布。"""

    def __init__(self, skill_code: str, *, stage: Optional[str] = None):
        self.skill_code = skill_code
        self.stage = stage
        stage_part = f"阶段「{stage}」所需 " if stage else ""
        super().__init__(f"{stage_part}Skill「{skill_code}」{SKILL_NOT_REGISTERED_MSG}")


async def get_registered_skill(skill_code: str) -> Optional[Dict[str, Any]]:
    """仅查 Skill 库已发布版本；不读取代码库 skills/ 目录。"""
    if not skill_code:
        return None
    from app.services.drama_skill_service import get_drama_skill_service

    return await get_drama_skill_service().get_published(skill_code)


async def require_registered_skill(
    skill_code: str,
    *,
    stage: Optional[str] = None,
) -> Dict[str, Any]:
    skill = await get_registered_skill(skill_code)
    if not skill:
        raise SkillNotRegisteredError(skill_code, stage=stage)
    return skill


async def resolve_stage_skill(
    stage: str,
    *,
    required: bool = True,
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    解析阶段对应 Skill。
    required=True 且映射存在但未注册时抛出 SkillNotRegisteredError。
    """
    if stage in STAGES_WITHOUT_SKILL:
        return None, None
    skill_code = STAGE_SKILL_MAP.get(stage)
    if not skill_code:
        return None, None
    skill = await get_registered_skill(skill_code)
    if not skill and required:
        raise SkillNotRegisteredError(skill_code, stage=stage)
    return skill_code, skill


def skill_trace_for_stage(
    stage: str,
    skill_code: Optional[str],
    skill_doc: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """生成唯一的 Skill 过程步骤（校验 + 加载合并为一步）。"""
    from app.core.drama.agent_process_trace import make_trace_step

    if skill_doc and skill_code:
        block = format_skill_for_agent_prompt(skill_doc)
        return make_trace_step(
            "skill_load",
            "skill",
            "加载 Skill 模板（Skill 库）",
            status="ok",
            summary=f"{skill_doc.get('name')} ({skill_code})",
            detail=block[:800],
        )
    if stage in STAGES_WITHOUT_SKILL:
        return make_trace_step(
            "skill_load",
            "skill",
            "加载 Skill 模板",
            status="skip",
            summary=PRODUCTION_SKILL_SKIP_SUMMARY,
            detail=PRODUCTION_SKILL_SKIP_DETAIL,
        )
    return make_trace_step(
        "skill_load",
        "skill",
        "加载 Skill 模板",
        status="skip",
        summary=f"阶段 {stage} 无默认 Skill",
        detail="当前阶段未映射 Skill；创作助手将按通用指令回复。",
    )


def format_skill_for_agent_prompt(skill: Dict[str, Any]) -> str:
    """将 Skill 库文档格式化为创作助手 system 注入块（完整正文）。"""
    code = skill.get("skill_code") or ""
    name = skill.get("name") or code
    version = skill.get("version") or ""
    source = skill.get("source_type") or skill.get("source") or "online"
    content = (skill.get("skill_content_md") or skill.get("system_markdown") or "").strip()
    header = f"【Skill 库已注册 · {name} ({code}) v{version} · 来源:{source}】"
    if not content:
        return f"{header}\n（Skill 正文为空，请在 Skill 库补充 SKILL.md 内容并发布。）"
    body = f"{header}\n\n{content}"
    if code == "skill.concept":
        body = f"{body}\n\n{CONCEPT_OUTPUT_OVERRIDE}"
    if code == "skill.production":
        body = f"{body}\n\n{PRODUCTION_OUTPUT_OVERRIDE}"
    return body


def format_skill_hint_json(skill: Dict[str, Any], skill_code: str) -> str:
    import json

    return json.dumps(
        {
            "skill_code": skill_code,
            "name": skill.get("name"),
            "stage": skill.get("stage"),
            "version": skill.get("version"),
            "source_type": skill.get("source_type") or skill.get("source"),
            "registered": True,
            "tag": (skill.get("skill_meta") or {}).get("tag") or skill.get("description"),
            "content_preview": (
                (skill.get("skill_content_md") or skill.get("system_markdown") or "")[:2000]
            ),
        },
        ensure_ascii=False,
    )
