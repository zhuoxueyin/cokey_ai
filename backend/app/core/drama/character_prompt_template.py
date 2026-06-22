"""角色 prompt 组装工具 — 规范正文以 Skill 库 skill.character 为准。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.drama.character_ref_analysis import (
    empty_ref_analysis,
    merge_style_and_ref_analysis,
)
from app.core.drama.character_image_tasks import (
    FENCE_CARD_PROMPT,
    FENCE_IMAGE_TASKS,
    FENCE_LOOK_PROMPT,
    build_image_task_json_block,
)

TEMPLATE_VERSION = "4.2"

CHARACTER_WORKFLOW_PHASES: List[tuple[str, str, str]] = [
    ("character_design", "角色设计", "背景、身份、性格、性别、关系、目标等宏观设定"),
    ("look_design", "角色定妆图设计", "画风、形象、服饰、头像气质、配色、线条；单视角"),
    ("character_card", "角色卡片", "多角度、多表情、多动作、服饰细节、道具、武器；16:9"),
]

CARD_DIMENSION_KEYS: List[tuple[str, str]] = [
    ("background_zh", "背景"),
    ("appearance_zh", "形象"),
    ("expression_zh", "表情"),
    ("action_zh", "动作"),
    ("costume_zh", "服饰"),
    ("style_zh", "风格"),
    ("accessories_zh", "配件"),
    ("tools_weapons_zh", "工具/武器"),
]

LOOK_PROMPT_SECTION_ORDER: List[tuple[str, str]] = [
    ("layout", "单视角构图"),
    ("subject", "主体"),
    ("appearance", "形象"),
    ("costume", "服饰"),
    ("color_palette", "配色"),
    ("line_art", "线条"),
    ("style_tokens", "风格 token"),
    ("character_suffix", "风格后缀"),
]

CARD_PROMPT_SECTION_ORDER: List[tuple[str, str]] = [
    ("layout", "16:9 设定卡构图"),
    ("subject", "主体"),
    ("appearance", "形象"),
    ("expression", "多表情"),
    ("action", "多动作"),
    ("costume", "服饰细节"),
    ("accessories", "配件"),
    ("tools_weapons", "道具/武器"),
    ("background", "背景"),
    ("style_tokens", "风格 token"),
    ("character_suffix", "风格后缀"),
]

DEFAULT_LOOK_LAYOUT_EN = (
    "character costume design portrait, single unified illustration, one view only, "
    "no turn-around, no character sheet, no multiple panels, no expression sheet, "
    "head and shoulders or three-quarter body, clear facial features and hairstyle, "
    "representative outfit and color palette, plain solid color background, "
    "clean studio backdrop, no environmental storytelling, clean composition"
)

DEFAULT_CARD_LAYOUT_EN = (
    "character reference sheet, character profile card, 16:9 widescreen aspect ratio, "
    "single unified illustration, one image only, multiple angles turn-around, "
    "multiple facial expressions, multiple action poses, outfit and accessory details, "
    "key props and weapons, single character only, organized layout, "
    "minimal neutral background blocks, character-focused composition, character name text label"
)


def export_template_document() -> Dict[str, Any]:
    """同步导出占位；运行时请用 export_template_document_async 读取 Skill 库。"""
    return {
        "version": TEMPLATE_VERSION,
        "skill_code": "skill.character",
        "source": "skill_library_required",
        "workflow_phases": [
            {"key": k, "label": label, "summary": summary}
            for k, label, summary in CHARACTER_WORKFLOW_PHASES
        ],
        "markdown": (
            "角色生图规范已内聚于 Skill 库 `skill.character`（skills/skill_character/SKILL.md）。"
            "请确保已在 Skill 库发布；API 将返回已发布 Skill 正文。"
        ),
        "look_section_order": [{"key": k, "label": v} for k, v in LOOK_PROMPT_SECTION_ORDER],
        "card_section_order": [{"key": k, "label": v} for k, v in CARD_PROMPT_SECTION_ORDER],
        "section_order": [{"key": k, "label": v} for k, v in CARD_PROMPT_SECTION_ORDER],
        "card_dimensions": [{"key": k, "label": v} for k, v in CARD_DIMENSION_KEYS],
        "output_fields": [
            "character_design",
            "look_design",
            "card_dimensions",
            "look-prompt",
            "card-prompt",
            "character-image-tasks",
            "react_trace",
            "status",
        ],
        "image_task_fences": {
            "look_prompt": FENCE_LOOK_PROMPT,
            "card_prompt": FENCE_CARD_PROMPT,
            "tasks_json": FENCE_IMAGE_TASKS,
        },
    }


async def export_template_document_async() -> Dict[str, Any]:
    """从 Skill 库已发布的 skill.character 导出规范正文。"""
    from app.core.drama.skill_registry import get_registered_skill

    skill = await get_registered_skill("skill.character")
    base = export_template_document()
    if skill:
        content = (skill.get("skill_content_md") or skill.get("system_markdown") or "").strip()
        base.update(
            {
                "version": skill.get("version") or TEMPLATE_VERSION,
                "source": "skill_library",
                "markdown": content,
            }
        )
        return base
    base["source"] = "fallback_unregistered"
    return base


def analyze_style_for_character(style_doc: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """从绑定风格文档提炼 style_analysis（与 style_context.resolve_style_context 同源）。"""
    if not style_doc:
        return {
            "render_class": "live_action",
            "style_summary_zh": "",
            "style_summary_en": "",
            "character_suffix_en": "",
            "image_positive_en": "",
            "image_negative_en": "",
            "trait_tags": [],
            "color_palette": [],
        }
    mp = style_doc.get("model_prompts") or {}
    proto = style_doc.get("model_protocol") or {}
    visual = style_doc.get("visual") or {}
    return {
        "render_class": style_doc.get("render_class") or "live_action",
        "style_summary_zh": (mp.get("style_summary_zh") or style_doc.get("name") or "").strip(),
        "style_summary_en": (mp.get("style_summary_en") or "").strip(),
        "character_suffix_en": (mp.get("character_suffix_en") or "").strip(),
        "image_positive_en": (mp.get("image_positive_en") or "").strip(),
        "image_negative_en": (mp.get("image_negative_en") or "").strip(),
        "trait_tags": list(proto.get("trait_tags") or []),
        "color_palette": list(visual.get("color_palette") or []),
    }


def build_character_design(
    *,
    name: str = "",
    role: str = "",
    gender_zh: str = "",
    age_range_zh: str = "",
    description_zh: str = "",
    identity_zh: str = "",
    background_zh: str = "",
    personality_zh: str = "",
    story_function_zh: str = "",
    relationships_zh: str = "",
    goals_zh: str = "",
    conflicts_zh: str = "",
    status: str = "draft",
) -> Dict[str, Any]:
    """Step 4.1：宏观角色设计（不含定妆 prompt）。"""
    desc = description_zh.strip()
    display_name = name.strip() or "角色"
    return {
        "name": display_name,
        "role": role.strip() or "配角",
        "gender_zh": gender_zh.strip() or "待补充",
        "age_range_zh": age_range_zh.strip() or "待补充",
        "identity_zh": identity_zh.strip() or desc[:200] or "待补充",
        "background_zh": background_zh.strip() or desc[:300] or "待补充",
        "personality_zh": personality_zh.strip() or "待补充",
        "story_function_zh": story_function_zh.strip() or "待补充",
        "relationships_zh": relationships_zh.strip() or "待补充",
        "goals_zh": goals_zh.strip() or "待补充",
        "conflicts_zh": conflicts_zh.strip() or "待补充",
        "status": status if status in ("draft", "ready") else "draft",
    }


def build_look_design(
    *,
    character_design: Dict[str, Any],
    fused_style: Optional[Dict[str, Any]] = None,
    appearance_zh: str = "",
    costume_zh: str = "",
    avatar_notes_zh: str = "",
    color_palette_zh: str = "",
    line_art_zh: str = "",
    accessories_zh: str = "",
    status: str = "draft",
) -> Dict[str, Any]:
    """Step 4.2：定妆图设计字段（单视角视觉基底）。"""
    fused = fused_style or {}
    render_notes = (fused.get("style_summary_zh") or fused.get("render_class") or "").strip()
    palette = color_palette_zh.strip()
    if not palette and fused.get("color_palette_en"):
        palette = str(fused.get("color_palette_en"))
    line = line_art_zh.strip() or (fused.get("line_art_en") or "").strip()
    return {
        "render_notes_zh": render_notes or "待补充",
        "appearance_zh": appearance_zh.strip() or "待补充",
        "costume_zh": costume_zh.strip() or "待补充",
        "avatar_notes_zh": avatar_notes_zh.strip() or "待补充",
        "color_palette_zh": palette or "待补充",
        "line_art_zh": line or "待补充",
        "accessories_zh": accessories_zh.strip() or "无",
        "character_design_ref": character_design.get("name") or "",
        "status": status if status in ("draft", "ready") else "draft",
    }


def analyze_character_description(
    *,
    name: str = "",
    role: str = "",
    description_zh: str = "",
    identity_zh: str = "",
    appearance_zh: str = "",
    personality_zh: str = "",
    background_zh: str = "",
    expression_zh: str = "",
    action_zh: str = "",
    costume_zh: str = "",
    style_zh: str = "",
    accessories_zh: str = "",
    tools_weapons_zh: str = "",
    card_copy_zh: str = "",
    gender_zh: str = "",
    age_range_zh: str = "",
) -> Dict[str, Any]:
    """Step 4.3 辅助：结构化八维 card_dimensions + 宏观 character_design。"""
    desc = description_zh.strip()
    card_dimensions = {
        "background_zh": background_zh.strip() or desc[:120],
        "appearance_zh": appearance_zh.strip() or desc[:500],
        "expression_zh": expression_zh.strip() or "待补充",
        "action_zh": action_zh.strip() or "自然站立",
        "costume_zh": costume_zh.strip() or desc[:200],
        "style_zh": style_zh.strip(),
        "accessories_zh": accessories_zh.strip() or "无",
        "tools_weapons_zh": tools_weapons_zh.strip() or "无",
    }
    display_name = name.strip() or "角色"
    copy = card_copy_zh.strip() or f"{display_name} · {identity_zh.strip() or role.strip() or '角色'}"[:40]
    character_design = build_character_design(
        name=display_name,
        role=role,
        gender_zh=gender_zh,
        age_range_zh=age_range_zh,
        description_zh=desc,
        identity_zh=identity_zh,
        background_zh=background_zh or card_dimensions["background_zh"],
        personality_zh=personality_zh,
    )
    return {
        "name": display_name,
        "role": role.strip() or "配角",
        "identity_zh": identity_zh.strip() or desc[:200],
        "personality_zh": personality_zh.strip(),
        "card_copy_zh": copy,
        "card_dimensions": card_dimensions,
        "character_design": character_design,
    }


def _join_prompt_parts(parts: List[str]) -> str:
    return ", ".join(p.strip().rstrip(",") for p in parts if p and p.strip())


def _style_sections(fused: Dict[str, Any], style_analysis: Dict[str, Any]) -> tuple[List[str], str, str]:
    tokens = list(fused.get("style_tokens_en") or [])
    suffix = (fused.get("character_suffix_en") or style_analysis.get("character_suffix_en") or "").strip()
    extra_style = _join_prompt_parts(
        [
            fused.get("line_art_en") or "",
            fused.get("lighting_en") or "",
            fused.get("texture_en") or "",
        ]
    )
    if extra_style:
        tokens = list(dict.fromkeys(tokens + [extra_style]))[:8]
    style_token_str = _join_prompt_parts(tokens[:8])
    return tokens, style_token_str, suffix


def _base_negative(fused: Dict[str, Any], style_analysis: Dict[str, Any], *, extra: str) -> str:
    base_neg = (fused.get("image_negative_en") or style_analysis.get("image_negative_en") or "").strip()
    return _join_prompt_parts([base_neg, extra])


def build_look_prompt_pack(
    style_analysis: Dict[str, Any],
    character_design: Dict[str, Any],
    look_design: Dict[str, Any],
    *,
    ref_style_analysis: Optional[Dict[str, Any]] = None,
    fused_style: Optional[Dict[str, Any]] = None,
    layout_en: str = "",
    subject_en: str = "",
    appearance_en: str = "",
    costume_en: str = "",
    color_palette_en: str = "",
    line_art_en: str = "",
    aspect_ratio: str = "3:4",
) -> Dict[str, Any]:
    """Step 4.2：单视角定妆图 prompt_pack。"""
    fused = fused_style or merge_style_and_ref_analysis(
        style_analysis,
        ref_style_analysis if ref_style_analysis else empty_ref_analysis(has_refs=False),
    )
    _, style_token_str, suffix = _style_sections(fused, style_analysis)
    layout = layout_en.strip() or DEFAULT_LOOK_LAYOUT_EN
    subject = subject_en.strip() or _join_prompt_parts(
        [character_design.get("gender_zh", ""), character_design.get("age_range_zh", "")]
    )
    sections_en = {
        "subject": subject,
        "appearance": appearance_en.strip() or look_design.get("appearance_zh", ""),
        "costume": costume_en.strip() or look_design.get("costume_zh", ""),
        "color_palette": color_palette_en.strip() or look_design.get("color_palette_zh", ""),
        "line_art": line_art_en.strip() or look_design.get("line_art_zh", ""),
        "style_tokens": style_token_str,
        "character_suffix": suffix,
    }
    positive = _join_prompt_parts(
        [
            layout,
            sections_en["subject"],
            sections_en["appearance"],
            sections_en["costume"],
            sections_en["color_palette"],
            sections_en["line_art"],
            sections_en["style_tokens"],
            sections_en["character_suffix"],
        ]
    )
    look_neg = (
        "turn-around, multiple views, character sheet, expression sheet, action sheet, "
        "multiple panels, split screen, comic grid, collage, multiple people, deformed face, "
        "complex environment, cinematic scenery, architecture interior, landscape background"
    )
    negative = _base_negative(fused, style_analysis, extra=look_neg)
    return {
        "aspect_ratio": aspect_ratio,
        "image_count": 1,
        "layout_en": layout,
        "positive_en": positive,
        "negative_en": negative,
        "sections_en": sections_en,
    }


def build_character_card_prompt_pack(
    style_analysis: Dict[str, Any],
    character_analysis: Dict[str, Any],
    *,
    ref_style_analysis: Optional[Dict[str, Any]] = None,
    fused_style: Optional[Dict[str, Any]] = None,
    layout_en: str = "",
    subject_en: str = "",
    appearance_en: str = "",
    expression_en: str = "",
    action_en: str = "",
    costume_en: str = "",
    accessories_en: str = "",
    tools_weapons_en: str = "",
    background_en: str = "",
    style_tokens: Optional[List[str]] = None,
    locked_tokens: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Step 4.3：16:9 角色卡 prompt_pack（多角度/多表情/多动作）。"""
    fused = fused_style or merge_style_and_ref_analysis(
        style_analysis,
        ref_style_analysis if ref_style_analysis else empty_ref_analysis(has_refs=False),
    )
    tokens, style_token_str, suffix = _style_sections(fused, style_analysis)
    if style_tokens:
        tokens = list(dict.fromkeys(list(style_tokens) + tokens))[:8]
        style_token_str = _join_prompt_parts(tokens)
    card_copy = character_analysis.get("card_copy_zh") or character_analysis.get("name") or ""
    label = card_copy.strip() or character_analysis.get("name", "").strip()
    text_part = f'character name text "{label}"' if label else "character name text label"
    layout = layout_en.strip() or f"{DEFAULT_CARD_LAYOUT_EN}, {text_part}"

    sections_en = {
        "subject": subject_en.strip(),
        "appearance": appearance_en.strip(),
        "expression": expression_en.strip(),
        "action": action_en.strip(),
        "costume": costume_en.strip(),
        "accessories": accessories_en.strip(),
        "tools_weapons": tools_weapons_en.strip(),
        "background": background_en.strip(),
        "style_tokens": style_token_str,
        "character_suffix": suffix,
    }
    positive = _join_prompt_parts(
        [
            layout,
            sections_en["subject"],
            sections_en["appearance"],
            sections_en["expression"],
            sections_en["action"],
            sections_en["costume"],
            sections_en["accessories"],
            sections_en["tools_weapons"],
            sections_en["background"],
            sections_en["style_tokens"],
            sections_en["character_suffix"],
        ]
    )
    card_neg = (
        "single portrait only, one view only, no turn-around, wrong aspect ratio, not 16:9, "
        "multiple panels as separate images, collage, duplicate character, multiple people, "
        "deformed face, extra limbs, watermark, illegible text, blurry, heavy environment narrative"
    )
    negative = _base_negative(fused, style_analysis, extra=card_neg)

    locked = locked_tokens or []
    if not locked:
        for chunk in (appearance_en, costume_en, accessories_en):
            for part in chunk.split(","):
                w = part.strip()
                if w and len(w.split()) <= 5:
                    locked.append(w)
    locked = list(dict.fromkeys(locked))[:8]

    design = character_analysis.get("character_design") or build_character_design(
        name=character_analysis.get("name", ""),
        role=character_analysis.get("role", ""),
        identity_zh=character_analysis.get("identity_zh", ""),
        personality_zh=character_analysis.get("personality_zh", ""),
    )
    look = build_look_design(
        character_design=design,
        fused_style=fused,
        appearance_zh=(character_analysis.get("card_dimensions") or {}).get("appearance_zh", ""),
        costume_zh=(character_analysis.get("card_dimensions") or {}).get("costume_zh", ""),
    )

    return {
        "style_analysis": style_analysis,
        "ref_style_analysis": ref_style_analysis or empty_ref_analysis(has_refs=False),
        "fused_style": fused,
        "character_design": design,
        "look_design": look,
        "look_prompt_pack": build_look_prompt_pack(
            style_analysis,
            design,
            look,
            ref_style_analysis=ref_style_analysis,
            fused_style=fused,
        ),
        "character_analysis": character_analysis,
        "card_dimensions": character_analysis.get("card_dimensions") or {},
        "card_copy_zh": card_copy,
        "locked_tokens": locked,
        "card_prompt_pack": {
            "aspect_ratio": "16:9",
            "image_count": 1,
            "layout_en": layout,
            "positive_en": positive,
            "negative_en": negative,
            "sections_en": sections_en,
        },
        "status": "draft",
    }


def build_character_prompt_pack(
    style_analysis: Dict[str, Any],
    character_analysis: Dict[str, Any],
    **kwargs: Any,
) -> Dict[str, Any]:
    """兼容别名 → build_character_card_prompt_pack；保留 prompt_pack 字段。"""
    out = build_character_card_prompt_pack(style_analysis, character_analysis, **kwargs)
    out["prompt_pack"] = out["card_prompt_pack"]
    return out


def build_character_image_task_entries(
    *,
    character_name: str,
    look_prompt_markdown: str,
    card_prompt_markdown: str,
    look_negative_en: str,
    card_negative_en: str,
    look_aspect_ratio: str = "3:4",
    card_aspect_ratio: str = "16:9",
) -> Dict[str, str]:
    """服务端参考：由 prompt 正文 + 任务 JSON 组成完整出图输出块。"""
    tasks = [
        {
            "task_id": "look",
            "character_name": character_name,
            "label": f"{character_name}·定妆图",
            "aspect_ratio": look_aspect_ratio,
            "prompt_ref": FENCE_LOOK_PROMPT,
            "negative_en": look_negative_en,
            "image_count": 1,
        },
        {
            "task_id": "card",
            "character_name": character_name,
            "label": f"{character_name}·角色卡",
            "aspect_ratio": card_aspect_ratio,
            "prompt_ref": FENCE_CARD_PROMPT,
            "negative_en": card_negative_en,
            "image_count": 1,
        },
    ]
    return {
        FENCE_LOOK_PROMPT: look_prompt_markdown.strip(),
        FENCE_CARD_PROMPT: card_prompt_markdown.strip(),
        FENCE_IMAGE_TASKS: build_image_task_json_block(tasks),
    }


def format_character_session_guide(
    style_analysis: Dict[str, Any],
    *,
    ref_image_count: int = 0,
    ref_urls: Optional[List[str]] = None,
) -> str:
    """角色阶段注入：风格准备 + 三步流水线说明。"""
    import json

    has_refs = ref_image_count > 0
    ref_block = ""
    if has_refs:
        urls = ref_urls or []
        url_lines = "\n".join(f"- {u}" for u in urls[:6]) or "（见【用户 @ 引用资源】）"
        ref_block = f"""
【参考图 · 待 vision 分析（风格准备 Step 2）】
共 {ref_image_count} 张。你必须先「看」这些图（已随请求 multimodal 送入），仅提取：
风格 / 线条 / 配色 / 光影 / 材质笔触 → 写入 ref_style_analysis。
禁止从参考图复制：性别、长相、发型、服装、武器、身份。
{url_lines}
"""

    phases = "\n".join(
        f"  {i + 1}. {label} — {summary}"
        for i, (_, label, summary) in enumerate(CHARACTER_WORKFLOW_PHASES)
    )

    return f"""【角色生产 Skill · 三步流水线（skill.character v4.2）】

本回合按 Skill 分步推理（Observe→Think→Act→Finish），输出 Markdown + 出图任务 JSON。
宏观人物设定只来自用户文字；视觉风格来自「绑定风格 + 参考图（若有）」。

--- style_analysis（风格准备 Step 1 · 已解析）---
{json.dumps(style_analysis, ensure_ascii=False, indent=2)}
{ref_block}
--- 风格准备（0~3，不可跳步）---
Step 0 Observe → Step 1 解读 style_analysis → Step 2 参考图 vision（若有）→ Step 3 fused_style

--- 三步生产流水线（4.1 → 4.2 → 4.3，不可跳步）---
{phases}

【意图识别（先判再做）】
- **活跃角色**：以 Prompt 中「当前活跃角色」为准；用户未点名时禁止跳回更早角色
- 若用户在“补人物设定” → 只交付 Step 4.1（角色设计）
- 若用户在“出定妆图/形象图” → 先确认 4.1 ready，再交付 Step 4.2
- 若用户在“出角色卡八维/16:9 设定卡” → 先确认 4.1/4.2 ready，再交付 Step 4.3
- 除非用户明确要求“一次全出”，默认单轮只交付当前意图阶段，其他阶段标注 pending

Step 4.1 角色设计：Markdown 表格（背景/身份/性格/性别/关系/目标），不出 prompt
Step 4.2 定妆设计 + ```{FENCE_LOOK_PROMPT}```：单视角 portrait/3:4，纯色/干净背景，禁止多视角/表情集/环境叙事
Step 4.3 角色卡八维 + ```{FENCE_CARD_PROMPT}```：16:9 设定卡，多角度/多表情/多动作/道具武器，背景信息从简不喧宾夺主

--- 出图输出格式（一键出图解析入口）---
1. 先给【本轮可交付结果】与【交付物清单】
2. 再给 Markdown 主力 prompt：```{FENCE_LOOK_PROMPT}``` 与 ```{FENCE_CARD_PROMPT}```（英文生图描述）
3. 最后给 ```{FENCE_IMAGE_TASKS}``` JSON（aspect_ratio、prompt_ref、negative_en、image_count）
   · 正向 prompt 读 Markdown 块；负向与尺寸在 JSON

回复须含：可交付结果摘要、设定 Markdown 表格、所需 prompt 块、character-image-tasks JSON。
`### ReAct 执行记录`保留为精简版（<=6 行），放在回复末尾。"""
