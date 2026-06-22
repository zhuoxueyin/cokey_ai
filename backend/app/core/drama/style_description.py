"""风格描述 Markdown：单一编辑入口，解析为 model_prompts / visual 供 Agent 与生图使用。"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

# v2 规范：视觉维度独立分节（与 style_description_builder.VISUAL_SECTIONS 一致）
VISUAL_SPEC_SECTIONS: List[Tuple[str, str]] = [
    ("category", "画风大类"),
    ("artist_refs", "画师/工作室参考"),
    ("era_texture", "年代质感"),
    ("line_control", "线条与轮廓控制"),
    ("lighting_color", "光影与色彩"),
    ("palette_strategy", "配色搭配"),
    ("atmosphere", "氛围气质"),
    ("materials", "材质细节"),
    ("quality", "画质要求"),
    ("taboos", "约束禁忌"),
]

SECTION_DEFS: List[Tuple[str, str]] = [
    ("summary", "风格摘要"),
    *VISUAL_SPEC_SECTIONS,
    ("characters", "人物角色"),
    ("scenes", "场景描述"),
    ("colors", "色彩倾向"),
    ("references", "代表作品"),
    ("image_prompt", "生图提示词参考"),
    ("video_prompt", "生视频提示词参考"),
]

# 旧版「风格特点」合并节（兼容历史数据）
_LEGACY_SECTION_TITLES: Dict[str, str] = {"风格特点": "traits"}

_TITLE_TO_KEY = {title: key for key, title in SECTION_DEFS}
_TITLE_TO_KEY.update(_LEGACY_SECTION_TITLES)


def style_description_template(name: str = "") -> str:
    """空模板，供新建风格时使用（v2 分节规范）。"""
    head = f"# {name}\n\n" if name else ""
    blocks = [head]
    hints = {
        "summary": "2–4 句概括美学定位、叙事气质、适用场景与 AI 出图/出视频要点。",
        "category": "如：二维赛璐璐动画 / 真人电影摄影 / 三维风格化渲染。",
        "artist_refs": "具体画师、摄影指导、工作室或参考 IP 美术方向（勿逐像素临摹）。",
        "era_texture": "年代、媒介、颗粒/印刷/胶片/数字渲染质感。",
        "line_control": "勾线粗细、轮廓策略、silhouette 与内外线关系。",
        "lighting_color": "主光方向、光比、色温、阴影层级、LUT 倾向。",
        "palette_strategy": "主色/辅色/点缀色组织原则与叙事用色。",
        "atmosphere": "情绪基调、空气透视、天气与叙事张力。",
        "materials": "皮肤/布料/金属/环境材质的可执行描述。",
        "quality": "分辨率、锐度、完成度、平台画幅（9:16 等）。",
        "taboos": "须规避的错误美学（如 3D 写实、错误比例等）。",
        "characters": "中文造型要点 + 空行 + English character prompt fragment。",
        "scenes": "中文场景构图要点 + 空行 + English scene prompt fragment。",
        "colors": "主色与辅助色，逗号或换行分隔。",
        "references": "每行一部参考作品，可带年份。",
        "image_prompt": "English positive prompt for image models (40–80 words).",
        "video_prompt": "English positive prompt for video models (20–40 words).",
    }
    for key, title in SECTION_DEFS:
        blocks.append(f"## {title}\n\n{hints.get(key, '')}\n")
    return "\n".join(blocks).strip() + "\n"


def parse_style_description_md(text: str) -> Dict[str, str]:
    if not text or not str(text).strip():
        return {}
    sections: Dict[str, str] = {}
    current_key: str | None = None
    current_lines: List[str] = []

    for line in str(text).splitlines():
        stripped = line.strip()
        matched_key = None
        if stripped.startswith("##"):
            heading = stripped.lstrip("#").strip()
            matched_key = _TITLE_TO_KEY.get(heading)
        if matched_key:
            if current_key is not None:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = matched_key
            current_lines = []
        elif current_key is not None:
            current_lines.append(line)

    if current_key is not None:
        sections[current_key] = "\n".join(current_lines).strip()
    return sections


def _split_lines(value: str) -> List[str]:
    if not value:
        return []
    parts: List[str] = []
    for line in value.replace(",", "\n").splitlines():
        s = line.strip().lstrip("-•·").strip()
        if s and not s.startswith("（以上作品"):
            parts.append(s)
    return parts


def _split_csv(value: str) -> List[str]:
    if not value:
        return []
    return [p.strip() for p in re.split(r"[,，、\n]", value) if p.strip()]


def _extract_english_suffix(section: str) -> str:
    """人物/场景节末尾通常为英文 prompt，取最后一段 ASCII 为主。"""
    text = (section or "").strip()
    if not text:
        return ""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    if len(blocks) >= 2 and re.search(r"[a-zA-Z]", blocks[-1]):
        return blocks[-1][:1200]
    if re.search(r"[a-zA-Z]", text):
        return text[:1200]
    return ""


def _build_style_summary_zh(sections: Dict[str, str]) -> str:
    parts: List[str] = []
    summary = sections.get("summary", "").strip()
    if summary:
        parts.append(summary)
    traits = sections.get("traits", "").strip()
    if traits:
        parts.append(traits)
    for key, title in VISUAL_SPEC_SECTIONS:
        body = sections.get(key, "").strip()
        if body:
            parts.append(f"【{title}】\n{body}")
    return "\n\n".join(parts)


def derive_from_sections(sections: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, Any]]:
    style_summary_zh = _build_style_summary_zh(sections)

    model_prompts: Dict[str, str] = {}
    if style_summary_zh:
        model_prompts["style_summary_zh"] = style_summary_zh
    if sections.get("image_prompt"):
        model_prompts["image_positive_en"] = sections["image_prompt"].strip()
    if sections.get("video_prompt"):
        model_prompts["video_positive_en"] = sections["video_prompt"].strip()

    char_en = _extract_english_suffix(sections.get("characters", ""))
    if char_en:
        model_prompts["character_suffix_en"] = char_en
    scene_en = _extract_english_suffix(sections.get("scenes", ""))
    if scene_en:
        model_prompts["scene_suffix_en"] = scene_en

    visual: Dict[str, Any] = {}
    refs = _split_lines(sections.get("references", ""))
    if refs:
        visual["reference_films"] = refs
    colors = _split_csv(sections.get("colors", ""))
    if colors:
        visual["color_palette"] = colors

    return model_prompts, visual


def legacy_doc_to_markdown(doc: Dict[str, Any]) -> str:
    existing = doc.get("style_description_md")
    if existing and str(existing).strip():
        return str(existing).strip()

    mp = doc.get("model_prompts") or {}
    visual = doc.get("visual") or {}
    name = doc.get("name") or ""

    blocks = [f"# {name}\n" if name else ""]
    section_content: Dict[str, str] = {
        "summary": mp.get("style_summary_zh") or "",
        "characters": mp.get("character_suffix_en") or "",
        "scenes": mp.get("scene_suffix_en") or "",
        "colors": ", ".join(visual.get("color_palette") or []),
        "references": "\n".join(visual.get("reference_films") or []),
        "image_prompt": mp.get("image_positive_en") or "",
        "video_prompt": mp.get("video_positive_en") or "",
    }
    for key, title in SECTION_DEFS:
        body = section_content.get(key, "")
        blocks.append(f"## {title}\n\n{body}\n")
    return "\n".join(b for b in blocks if b).strip() + "\n"


def enrich_style_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """写入 style_description_md 时同步派生 model_prompts / visual。"""
    out = dict(data)
    md = out.get("style_description_md")
    if md is not None and str(md).strip():
        out["style_description_md"] = str(md).strip()
        sections = parse_style_description_md(out["style_description_md"])
        mp, visual = derive_from_sections(sections)
        out["model_prompts"] = {**(out.get("model_prompts") or {}), **mp}
        merged_visual = {**(out.get("visual") or {}), **visual}
        if merged_visual:
            out["visual"] = merged_visual
    return out


def validate_for_publish(doc: Dict[str, Any]) -> None:
    md = doc.get("style_description_md")
    if md and str(md).strip():
        sections = parse_style_description_md(str(md))
        if not sections.get("summary"):
            raise ValueError("发布前须在风格描述中填写「风格摘要」")
        if not sections.get("image_prompt"):
            raise ValueError("发布前须在风格描述中填写「生图提示词参考」")
        return

    prompts = doc.get("model_prompts") or {}
    if not prompts.get("image_positive_en"):
        raise ValueError("发布前须填写生图提示词（风格描述 · 生图提示词参考）")
    if not (prompts.get("style_summary_zh") or prompts.get("style_summary_en")):
        raise ValueError("发布前须填写风格摘要")
