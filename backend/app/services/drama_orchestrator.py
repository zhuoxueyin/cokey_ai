"""短剧 Agent 主控（MVP：阶段路由 + Skill 占位回复）。"""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.logging_config import get_logger
from app.core.drama.skill_registry import (
    STAGE_SKILL_MAP,
    SKILL_NOT_REGISTERED_MSG,
    get_registered_skill,
)
from app.services.drama_knowledge_service import get_drama_knowledge_service
from app.services.drama_project_service import get_drama_project_service
from app.services.drama_style_service import get_drama_style_service

logger = get_logger()


class DramaOrchestrator:
    async def chat(
        self,
        project_id: str,
        message: str,
        stage_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        project_svc = get_drama_project_service()
        project = await project_svc.get_by_project_id(project_id)
        if not project:
            raise ValueError("项目不存在")

        stage = stage_override or project.get("stage", "init")
        skill_code = STAGE_SKILL_MAP.get(stage) or STAGE_SKILL_MAP.get("init", "skill.intake")
        skill = await get_registered_skill(skill_code)

        if STAGE_SKILL_MAP.get(stage) and not skill:
            return {
                "project_id": project_id,
                "stage": stage,
                "skill_code": skill_code,
                "error": True,
                "error_code": "skill_not_registered",
                "reply_markdown": (
                    f"**阶段 {stage} 所需 Skill「{skill_code}」{SKILL_NOT_REGISTERED_MSG}"
                ),
                "suggested_next": ["在 Skill 库注册并发布对应 Skill"],
            }

        style = None
        if project.get("style_preset_id"):
            style = await get_drama_style_service().get_by_style_id(project["style_preset_id"])

        knowledge = []
        if skill:
            knowledge = await get_drama_knowledge_service().search(
                query=message,
                category="short_drama",
                tags=skill.get("default_knowledge_tags"),
                top_k=4,
            )

        # MVP：尚未接入 LLM 网关，返回结构化占位 + 下一步建议
        reply = (
            f"【{stage} 阶段 · {skill_code}】已收到：{message[:200]}"
            f"\n\n（MVP 占位：后续将调用 ModelGateway 执行 Skill 并校验 JSON 输出）"
        )
        if style:
            reply += f"\n\n当前风格：**{style.get('name')}**"
        if knowledge:
            refs = "、".join(k["title"] for k in knowledge[:3])
            reply += f"\n\n引用知识：{refs}"

        next_steps = self._suggest_next(stage)
        return {
            "project_id": project_id,
            "stage": stage,
            "skill_code": skill_code,
            "skill_version": skill.get("version") if skill else None,
            "style_preset_id": project.get("style_preset_id"),
            "knowledge_refs": [k["entry_id"] for k in knowledge],
            "reply_markdown": reply,
            "suggested_next": next_steps,
        }

    @staticmethod
    def _suggest_next(stage: str) -> list[str]:
        flow = ["init", "concept", "outline", "script", "character", "scene", "storyboard", "prompt_pack", "production"]
        try:
            idx = flow.index(stage)
        except ValueError:
            return ["确认项目 Brief"]
        if idx + 1 < len(flow):
            labels = {
                "concept": "生成创意方向",
                "outline": "锁定剧集大纲",
                "script": "撰写单集剧本",
                "character": "完善角色卡",
                "scene": "设计场景卡",
                "storyboard": "拆分分镜表",
                "prompt_pack": "生成提示词包",
                "production": "推到无限画布",
            }
            return [labels.get(flow[idx + 1], f"进入 {flow[idx + 1]}")]
        return ["在无限画布完成出片"]


_orchestrator: Optional[DramaOrchestrator] = None


def get_drama_orchestrator() -> DramaOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = DramaOrchestrator()
    return _orchestrator
