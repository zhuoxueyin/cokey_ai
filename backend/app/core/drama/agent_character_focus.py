"""角色阶段 · 活跃角色与子步骤解析（避免跳回已完成角色）。"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.core.drama.agent_creation_pipeline import AgentCreationIntent, extract_subject

CHARACTER_SUBSTEPS: Dict[str, str] = {
    "character_design": "角色设计（宏观）",
    "look_design": "定妆图设计（单视角）",
    "character_card": "角色卡（16:9 设定卡）",
}

_CARD_RE = re.compile(r"16\s*:\s*9|角色卡|设定卡|八维|card", re.I)
_LOOK_RE = re.compile(r"定妆|形象图|look", re.I)
_DESIGN_RE = re.compile(r"人设|宏观|角色设计|人物设定|补人物")

_ASSISTANT_NAME_PATTERNS = [
    re.compile(r"确认[「\"]?([\u4e00-\u9fff·]{2,6})[」\"]?(?:角色|人设|定妆|方向|造型)"),
    re.compile(r"给[「\"]?([\u4e00-\u9fff·]{2,6})[」\"]?(?:设计|出|的|做)"),
    re.compile(r"补[「\"]?([\u4e00-\u9fff·]{2,6})[」\"]?"),
    re.compile(r"[「\"]([\u4e00-\u9fff·]{2,6})[」\"]的(?:角色|定妆|人设|造型)"),
    re.compile(r"([\u4e00-\u9fff·]{2,6})的(?:定妆|角色卡|人设|造型)"),
]
_IMAGE_TASK_NAME_RE = re.compile(r'"character_name"\s*:\s*"([^"]+)"')
_NEXT_OPTIONS_RE = re.compile(r"###\s*下一步可选[\s\S]*", re.I)

_NAME_STOP = frozenset(
    {
        "这个",
        "当前",
        "该角",
        "更滑稽",
        "更清秀",
        "更落魄",
        "更阴冷",
        "角色",
        "方向",
        "方案",
        "一位",
        "一个",
        "继续",
        "确认",
    }
)


@dataclass
class CharacterFocus:
    name: str = ""
    substep: str = ""
    source: str = "none"
    substep_label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "substep": self.substep,
            "substep_label": self.substep_label or CHARACTER_SUBSTEPS.get(self.substep, ""),
            "source": self.source,
        }


def _clean_name(raw: str) -> str:
    name = (raw or "").strip("·「」\"' ")
    if not name or len(name) > 8 or name in _NAME_STOP:
        return ""
    return name


def extract_character_substep(text: str) -> str:
    """从用户消息推断角色三步子步骤。"""
    t = (text or "").strip()
    if not t:
        return ""
    has_card = bool(_CARD_RE.search(t))
    has_look = bool(_LOOK_RE.search(t))
    has_design = bool(_DESIGN_RE.search(t))
    if has_design and not has_look and not has_card:
        return "character_design"
    if has_card and has_look:
        # 同时提及时按流水线顺序，本轮优先定妆（Skill 单轮一步）
        return "look_design"
    if has_card:
        return "character_card"
    if has_look:
        return "look_design"
    return ""


def extract_character_from_assistant(text: str) -> str:
    """从上轮助手「下一步可选」或正文提取活跃角色名。"""
    if not text:
        return ""
    section_m = _NEXT_OPTIONS_RE.search(text)
    section = section_m.group(0) if section_m else text[-2500:]
    for pat in _ASSISTANT_NAME_PATTERNS:
        m = pat.search(section)
        if m:
            name = _clean_name(m.group(1))
            if name:
                return name
    for m in _IMAGE_TASK_NAME_RE.finditer(text):
        name = _clean_name(m.group(1))
        if name:
            return name
    return ""


def resolve_character_focus(
    message: str,
    *,
    stored: Optional[Dict[str, Any]] = None,
    recent_messages: Optional[Sequence[Tuple[str, str]]] = None,
    intent: Optional[AgentCreationIntent] = None,
) -> CharacterFocus:
    """
    解析当前应服务的角色与子步骤。

    优先级：用户显式点名 > KV 活跃角色 > 上轮助手引导 > 近期用户消息。
    """
    substep = extract_character_substep(message)
    if not substep and stored:
        substep = (stored.get("character_substep") or "").strip()

    explicit = extract_subject(message) or (intent.subject if intent else "")
    if explicit:
        return CharacterFocus(
            name=explicit,
            substep=substep,
            source="user_explicit",
            substep_label=CHARACTER_SUBSTEPS.get(substep, ""),
        )

    stored_name = _clean_name((stored or {}).get("active_character") or "")
    if stored_name and intent and intent.intent_type in (
        "continue",
        "refine",
        "confirm",
        "advance",
    ):
        return CharacterFocus(
            name=stored_name,
            substep=substep,
            source="thread_context",
            substep_label=CHARACTER_SUBSTEPS.get(substep, ""),
        )

    roster = list((stored or {}).get("character_roster") or [])
    progress = (stored or {}).get("character_progress") or {}
    if roster and intent and intent.intent_type in (
        "continue",
        "refine",
        "confirm",
        "advance",
    ):
        from app.core.drama.agent_character_roster import pick_active_character_from_roster

        queued = pick_active_character_from_roster(
            roster, progress, preferred=stored_name
        )
        if queued:
            return CharacterFocus(
                name=queued,
                substep=substep,
                source="roster_queue",
                substep_label=CHARACTER_SUBSTEPS.get(substep, ""),
            )

    msgs = list(recent_messages or [])
    for role, content in reversed(msgs):
        if role != "assistant":
            continue
        from_assistant = extract_character_from_assistant(content)
        if from_assistant:
            return CharacterFocus(
                name=from_assistant,
                substep=substep,
                source="assistant_guidance",
                substep_label=CHARACTER_SUBSTEPS.get(substep, ""),
            )
        break

    for role, content in reversed(msgs):
        if role != "user":
            continue
        from_user = extract_subject(content)
        if from_user:
            return CharacterFocus(
                name=from_user,
                substep=substep,
                source="recent_user",
                substep_label=CHARACTER_SUBSTEPS.get(substep, ""),
            )

    if stored_name:
        return CharacterFocus(
            name=stored_name,
            substep=substep,
            source="thread_context_fallback",
            substep_label=CHARACTER_SUBSTEPS.get(substep, ""),
        )

    return CharacterFocus(
        substep=substep,
        source="none",
        substep_label=CHARACTER_SUBSTEPS.get(substep, ""),
    )


def format_character_focus_block(focus: CharacterFocus) -> str:
    """注入 Prompt 的活跃角色约束块。"""
    if not focus.name and not focus.substep:
        return ""
    lines = ["【当前活跃角色 · 必须遵守（高优先级）】"]
    if focus.name:
        src = {
            "user_explicit": "用户本轮点名",
            "thread_context": "线程上下文（上轮焦点）",
            "thread_context_fallback": "线程上下文",
            "roster_queue": "角色设计队列（按顺序）",
            "assistant_guidance": "上轮助手「下一步可选」",
            "recent_user": "近期用户消息",
        }.get(focus.source, focus.source)
        lines.append(f"- **活跃角色**：{focus.name}（来源：{src}）")
        lines.append(
            f"- 用户未再次点名时，**必须**继续「{focus.name}」；"
            f"**禁止**跳回对话中更早角色或默认第一个已设计角色。"
        )
        lines.append(f"- 开头 1~2 句须明确写出角色名「{focus.name}」。")
    if focus.substep:
        label = focus.substep_label or CHARACTER_SUBSTEPS.get(focus.substep, focus.substep)
        lines.append(f"- **本轮子步骤**：{label}（{focus.substep}）")
        if focus.substep == "look_design":
            lines.append("- 交付 Step 4.2：look_design + look-prompt；勿混出角色卡或多角色。")
        elif focus.substep == "character_card":
            lines.append("- 交付 Step 4.3：八维角色卡 + card-prompt（16:9）；勿退回宏观设计。")
        elif focus.substep == "character_design":
            lines.append("- 交付 Step 4.1：宏观角色设计表；勿提前出 look/card prompt。")
    if not focus.name:
        lines.append("- 未能锁定角色名：请根据上轮「下一步可选」与对话摘要推断；仍无法确定则向用户确认。")
    return "\n".join(lines)
