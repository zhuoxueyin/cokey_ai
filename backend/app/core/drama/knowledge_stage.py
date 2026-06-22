"""创作阶段常量 — 知识库分类「适用阶段」与检索过滤。"""
from __future__ import annotations

from typing import Dict, List

# 与 agent_creation_pipeline.PIPELINE_STAGES 对齐
CREATION_STAGES: List[Dict[str, str]] = [
    {"stage": "init", "label": "立项"},
    {"stage": "concept", "label": "创意脑暴"},
    {"stage": "outline", "label": "大纲"},
    {"stage": "script", "label": "剧本"},
    {"stage": "character", "label": "角色"},
    {"stage": "scene", "label": "场景"},
    {"stage": "storyboard", "label": "分镜"},
    {"stage": "production", "label": "生产"},
]

CREATION_STAGE_CODES: List[str] = [s["stage"] for s in CREATION_STAGES]
CREATION_STAGE_LABELS: Dict[str, str] = {s["stage"]: s["label"] for s in CREATION_STAGES}

VALID_CREATION_STAGES: frozenset[str] = frozenset(CREATION_STAGE_CODES)


def normalize_stage(stage: str | None) -> str:
    s = (stage or "").strip().lower()
    return s if s in VALID_CREATION_STAGES else "concept"


def validate_applicable_stages(stages: List[str] | None) -> List[str]:
    if not stages:
        return []
    out: List[str] = []
    seen: set[str] = set()
    for raw in stages:
        code = (raw or "").strip().lower()
        if code in VALID_CREATION_STAGES and code not in seen:
            seen.add(code)
            out.append(code)
    return out


def category_applies_to_stage(category_doc: Dict, stage: str) -> bool:
    """未配置 applicable_stages 时视为全阶段适用（向后兼容）。"""
    stages = category_doc.get("applicable_stages") or []
    if not stages:
        return True
    return stage in stages
