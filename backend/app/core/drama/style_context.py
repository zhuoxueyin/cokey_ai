"""统一风格上下文：一次读库 → 叙事块 + style_analysis（角色生图同源）。"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.core.drama.character_prompt_template import (
    analyze_style_for_character,
    format_character_session_guide,
)
from app.core.drama.style_model_protocol import build_model_protocol


def _build_prompt_block(style_id: str, style: Dict[str, Any]) -> str:
    mp = style.get("model_prompts") or {}
    visual = style.get("visual") or {}
    md = (style.get("style_description_md") or "").strip()
    if md:
        return (
            f"视觉风格（全对话锁定）：{style.get('name')}（{style_id}）\n"
            f"渲染类型：{style.get('render_class', '')}\n\n"
            f"{md[:4500]}"
        )
    refs = visual.get("reference_films") or []
    ref_line = "、".join(refs[:4]) if refs else "无"
    palette = visual.get("color_palette") or []
    palette_line = "、".join(palette[:6]) if palette else "无"
    summary = mp.get("style_summary_zh") or style.get("name") or ""
    return (
        f"视觉风格（全对话锁定）：{style.get('name')}（{style_id}）\n"
        f"渲染类型：{style.get('render_class', '')}\n"
        f"风格摘要：{summary}\n"
        f"参考作品：{ref_line}\n"
        f"色彩倾向：{palette_line}\n"
        f"出图正向词（节选）：{(mp.get('image_positive_en') or '')[:280]}"
    )


def _build_trace_detail(style: Dict[str, Any], style_analysis: Dict[str, Any]) -> str:
    md = (style.get("style_description_md") or "").strip()
    md_part = md[:2000] + ("…" if len(md) > 2000 else "") if md else ""
    analysis_part = json.dumps(style_analysis, ensure_ascii=False, indent=2)
    if md_part:
        return f"{md_part}\n\n--- style_analysis ---\n{analysis_part}"
    mp = style.get("model_prompts") or {}
    fallback = mp.get("style_summary_zh") or style.get("name") or ""
    if fallback:
        return f"{fallback}\n\n--- style_analysis ---\n{analysis_part}"
    return analysis_part


def format_character_style_guide(
    style_analysis: Dict[str, Any],
    *,
    ref_image_count: int = 0,
    ref_urls: Optional[List[str]] = None,
) -> str:
    """兼容别名 → format_character_session_guide。"""
    return format_character_session_guide(
        style_analysis,
        ref_image_count=ref_image_count,
        ref_urls=ref_urls,
    )


async def resolve_style_context(
    style_id: Optional[str],
    *,
    stage: Optional[str] = None,
    refs: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """一次读库，返回 prompt 块、style_analysis 与 trace 元数据。"""
    if not style_id:
        empty_analysis = analyze_style_for_character(None)
        return {
            "style_id": None,
            "style_doc": None,
            "prompt_block": "视觉风格：未绑定（通用创作）",
            "style_analysis": empty_analysis,
            "character_style_guide": "",
            "trace": {
                "status": "skip",
                "summary": "未绑定风格",
                "detail": "",
            },
        }

    from app.services.drama_style_service import get_drama_style_service

    doc = await get_drama_style_service().get_by_style_id(style_id)
    if not doc:
        empty_analysis = analyze_style_for_character(None)
        return {
            "style_id": style_id,
            "style_doc": None,
            "prompt_block": f"视觉风格：{style_id}（配置缺失，按通用创作）",
            "style_analysis": empty_analysis,
            "character_style_guide": "",
            "trace": {
                "status": "empty",
                "summary": style_id,
                "detail": "风格配置未找到，将按通用创作",
            },
        }

    enriched = dict(doc)
    if not enriched.get("model_protocol"):
        enriched["model_protocol"] = build_model_protocol(enriched)

    style_analysis = analyze_style_for_character(enriched)
    prompt_block = _build_prompt_block(style_id, enriched)
    character_style_guide = ""
    if stage == "character":
        from app.core.drama.agent_user_refs import extract_ref_image_urls

        ref_urls = extract_ref_image_urls(refs)
        character_style_guide = format_character_session_guide(
            style_analysis,
            ref_image_count=len(ref_urls),
            ref_urls=ref_urls,
        )
    trace_title_suffix = ""
    if stage == "character":
        trace_title_suffix = " · 已生成角色生图 style_analysis"

    return {
        "style_id": style_id,
        "style_doc": enriched,
        "prompt_block": prompt_block,
        "style_analysis": style_analysis,
        "character_style_guide": character_style_guide,
        "trace": {
            "status": "ok",
            "summary": f"{enriched.get('name') or style_id}（{style_id}）{trace_title_suffix}",
            "detail": _build_trace_detail(enriched, style_analysis),
        },
    }
