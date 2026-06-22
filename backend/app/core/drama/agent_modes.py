"""超级智能体快捷模式定义。"""
from __future__ import annotations

from typing import Any, Dict, List

from app.core.drama.agent_mode_prompts import MODE_SYSTEM_DIRECTIVES

AGENT_MODES: List[Dict[str, Any]] = [
    {
        "mode": "creative_short_drama",
        "name": "创意短剧",
        "description": "脑暴 → 剧本 → 分镜，竖屏爽剧节奏",
        "default_stage": "concept",
        "knowledge_categories": ["short_drama", "film", "animation_short", "platform", "camera_movement"],
        "system_directive": MODE_SYSTEM_DIRECTIVES["creative_short_drama"],
    },
    {
        "mode": "aigc_manga",
        "name": "AIGC漫剧",
        "description": "分格脚本与故事结构，视觉由风格与画布承接",
        "default_stage": "concept",
        "knowledge_categories": ["anime", "aigc", "animation_short", "film"],
        "system_directive": MODE_SYSTEM_DIRECTIVES["aigc_manga"],
    },
    {
        "mode": "mv",
        "name": "MV",
        "description": "音乐叙事、镜头与场景氛围",
        "default_stage": "concept",
        "knowledge_categories": ["film", "sound", "camera_movement"],
        "system_directive": MODE_SYSTEM_DIRECTIVES["mv"],
    },
    {
        "mode": "marketing_ad",
        "name": "营销广告",
        "description": "卖点、脚本与分镜，信息流适配",
        "default_stage": "concept",
        "knowledge_categories": ["short_drama", "platform", "camera_movement"],
        "system_directive": MODE_SYSTEM_DIRECTIVES["marketing_ad"],
    },
]

MODE_BY_CODE = {m["mode"]: m for m in AGENT_MODES}
