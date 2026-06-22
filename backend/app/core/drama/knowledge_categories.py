"""知识库内置 category 种子。"""
from __future__ import annotations

from typing import Any, Dict, List

KNOWLEDGE_CATEGORIES: List[Dict[str, Any]] = [
    {
        "code": "short_drama",
        "name": "短剧",
        "description": "竖屏爽剧、钩子与分集节奏",
        "builtin": True,
        "applicable_stages": ["concept", "outline", "script", "production", "platform"],
    },
    {
        "code": "film",
        "name": "电影",
        "description": "镜头语言、叙事结构与类型片",
        "builtin": True,
        "applicable_stages": ["concept", "outline", "script", "storyboard", "production"],
    },
    {
        "code": "anime",
        "name": "动漫",
        "description": "分格、角色一致性与条漫叙事",
        "builtin": True,
        "applicable_stages": ["concept", "character", "scene", "storyboard", "production"],
    },
    {
        "code": "animation_short",
        "name": "动画短片",
        "description": "独立动画短片叙事、节奏与视觉表达",
        "builtin": True,
        "applicable_stages": ["concept", "outline", "script", "character", "production"],
    },
    {
        "code": "aigc",
        "name": "AIGC",
        "description": "提示词工程与生成工作流",
        "builtin": True,
        "applicable_stages": ["character", "scene", "storyboard", "production"],
    },
    {
        "code": "cinematography",
        "name": "摄影",
        "description": "景别、机位与焦段基础",
        "builtin": True,
        "applicable_stages": ["storyboard", "scene", "production"],
    },
    {
        "code": "camera_movement",
        "name": "运镜",
        "description": "推/拉/摇/移/跟/升降/手持等镜头运动",
        "builtin": True,
        "applicable_stages": ["storyboard", "production"],
    },
    {
        "code": "color_light",
        "name": "色彩与光影",
        "description": "调色、氛围与情绪光",
        "builtin": True,
        "applicable_stages": ["scene", "storyboard", "production"],
    },
    {
        "code": "composition",
        "name": "构图",
        "description": "画面布局与视觉重心",
        "builtin": True,
        "applicable_stages": ["storyboard", "scene", "production"],
    },
    {
        "code": "performance",
        "name": "表演",
        "description": "角色情绪与对白表演",
        "builtin": True,
        "applicable_stages": ["script", "character"],
    },
    {
        "code": "sound",
        "name": "声音",
        "description": "配乐、音效与 MV 听感",
        "builtin": True,
        "applicable_stages": ["script", "outline", "production"],
    },
    {
        "code": "platform",
        "name": "平台规范",
        "description": "抖音/快手等信息流规范",
        "builtin": True,
        "applicable_stages": ["concept", "outline", "production"],
    },
    {
        "code": "custom",
        "name": "自定义",
        "description": "团队私有知识扩展",
        "builtin": True,
        "applicable_stages": [],
    },
]

# 创意脑暴阶段多类目融合检索（兼容旧引用，检索已改为按 applicable_stages）
CONCEPT_KNOWLEDGE_CATEGORIES: List[str] = [
    "short_drama",
    "film",
    "platform",
    "sound",
    "performance",
    "anime",
    "animation_short",
]
