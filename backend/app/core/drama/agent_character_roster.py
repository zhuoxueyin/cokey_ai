"""角色阶段 · 有序角色队列与三步进度（KV 持久化，抗 compact 丢记忆）。"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.core.drama.agent_character_focus import (
    CHARACTER_SUBSTEPS,
    _IMAGE_TASK_NAME_RE,
    _clean_name,
    extract_character_from_assistant,
    extract_subject,
)

_SUBSTEP_ORDER = ("character_design", "look_design", "character_card")

_ROSTER_HEADER_RE = re.compile(
    r"(?:核心人物|主要角色|角色列表|待设计角色)[:：]\s*([^\n]+)",
    re.I,
)
_ROSTER_DELIM_RE = re.compile(r"[\u4e00-\u9fff·]{2,6}")
_NAME_IN_HEADER_RE = re.compile(
    r"角色(?:设计|卡|定妆|设定)?[·\s—-]+([\u4e00-\u9fff·]{2,6})",
)
_JSON_NAME_RE = re.compile(r'"(?:name|character_name)"\s*:\s*"([^"]+)"')
_USER_LIST_RE = re.compile(
    r"(?:三[位个]|两[位个]|几[位个]|多[位个]|若干)?角色(?:是|有|包括|[:：])?\s*([^\n。；;]+)",
)

_NAME_STOP = frozenset(
    {
        "这个",
        "当前",
        "该角",
        "角色",
        "方向",
        "方案",
        "一位",
        "一个",
        "继续",
        "确认",
        "阶段",
        "场景",
        "分镜",
        "剧本",
        "大纲",
        "创意",
        "设计",
        "定妆",
        "风格",
        "上美",
    }
)


def _valid_name(raw: str) -> str:
    name = _clean_name(raw)
    if not name or name in _NAME_STOP:
        return ""
    return name


def _names_from_delimited(text: str) -> List[str]:
    out: List[str] = []
    for part in re.split(r"[、，,;/\s]+", text):
        name = _valid_name(part.strip())
        if name and name not in out:
            out.append(name)
    return out


def extract_character_names_from_text(text: str) -> List[str]:
    """从单条消息提取可能出现的角色名（保序去重）。"""
    if not text:
        return []
    found: List[str] = []

    def add(name: str) -> None:
        n = _valid_name(name)
        if n and n not in found:
            found.append(n)

    m = _ROSTER_HEADER_RE.search(text)
    if m:
        for n in _names_from_delimited(m.group(1)):
            add(n)

    m = _USER_LIST_RE.search(text)
    if m:
        for n in _names_from_delimited(m.group(1)):
            add(n)

    for m in _NAME_IN_HEADER_RE.finditer(text):
        add(m.group(1))

    for m in _JSON_NAME_RE.finditer(text):
        add(m.group(1))

    for m in _IMAGE_TASK_NAME_RE.finditer(text):
        add(m.group(1))

    subj = extract_subject(text)
    if subj:
        add(subj)

    from_assistant = extract_character_from_assistant(text)
    if from_assistant:
        add(from_assistant)

    return found


def infer_character_progress(name: str, content: str) -> Dict[str, bool]:
    """从助手交付物推断某角色三步完成情况。"""
    if not name or name not in content:
        return {"character_design": False, "look_design": False, "character_card": False}

    design = bool(
        re.search(rf"{re.escape(name)}.{0,40}(?:宏观|人设|character_design|角色设计表)", content, re.S)
        or re.search(rf"###\s*[^\n]*(?:设计|设定)[\s·]*{re.escape(name)}", content)
        or re.search(rf"角色设计[\s·]*{re.escape(name)}", content)
    )
    look = bool(re.search(r"```look-prompt", content) and name in content)
    card = bool(re.search(r"```card-prompt", content) and name in content)

    if re.search(rf"{re.escape(name)}.{0,80}```look-prompt", content, re.S):
        look = True
    if re.search(rf"{re.escape(name)}.{0,80}```card-prompt", content, re.S):
        card = True

    return {
        "character_design": design,
        "look_design": look,
        "character_card": card,
    }


def merge_progress(
    base: Dict[str, Dict[str, bool]],
    name: str,
    patch: Dict[str, bool],
) -> None:
    cur = dict(base.get(name) or {})
    for k in _SUBSTEP_ORDER:
        cur[k] = bool(cur.get(k) or patch.get(k))
    base[name] = cur


def sync_roster_from_messages(
    messages: Sequence[Dict[str, Any]],
    stored: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """扫描线程消息，合并角色队列与进度（写入 KV，不依赖 compact 摘要）。"""
    stored = stored or {}
    roster: List[str] = list(stored.get("character_roster") or [])
    progress: Dict[str, Dict[str, bool]] = {
        k: dict(v) for k, v in (stored.get("character_progress") or {}).items()
    }

    for msg in messages:
        role = msg.get("role")
        content = (msg.get("content") or "").strip()
        if not content or role not in ("user", "assistant"):
            continue
        for name in extract_character_names_from_text(content):
            if name not in roster:
                roster.append(name)
        if role == "assistant":
            for name in roster:
                merge_progress(progress, name, infer_character_progress(name, content))

    active = (stored.get("active_character") or "").strip()
    if active and active not in roster:
        roster.append(active)

    return {
        "character_roster": roster,
        "character_progress": progress,
        "active_character": active,
        "character_substep": (stored.get("character_substep") or "").strip(),
    }


def pick_next_substep(progress: Dict[str, bool]) -> str:
    for step in _SUBSTEP_ORDER:
        if not progress.get(step):
            return step
    return ""


def pick_active_character_from_roster(
    roster: List[str],
    progress: Dict[str, Dict[str, bool]],
    *,
    preferred: str = "",
) -> str:
    if preferred and preferred in roster:
        return preferred
    if preferred and preferred not in roster:
        return preferred
    for name in roster:
        p = progress.get(name) or {}
        if pick_next_substep(p):
            return name
    return roster[-1] if roster else ""


def resolve_active_character_with_roster(
    message: str,
    *,
    stored: Dict[str, Any],
    recent_messages: Optional[Sequence[Tuple[str, str]]] = None,
    explicit_name: str = "",
) -> Tuple[str, str]:
    """
    返回 (active_character, source_hint)。
    显式点名 > KV 活跃 > 队列中第一个未完成 > 助手引导。
    """
    roster: List[str] = list(stored.get("character_roster") or [])
    progress: Dict[str, Dict[str, bool]] = stored.get("character_progress") or {}

    if explicit_name:
        return explicit_name, "user_explicit"

    stored_active = _valid_name(stored.get("active_character") or "")
    if stored_active:
        return stored_active, "thread_roster"

    if roster:
        nxt = pick_active_character_from_roster(roster, progress)
        if nxt:
            return nxt, "roster_queue"

    for role, content in reversed(list(recent_messages or [])):
        if role != "assistant":
            continue
        name = extract_character_from_assistant(content)
        if name:
            return name, "assistant_guidance"
        break

    for role, content in reversed(list(recent_messages or [])):
        if role != "user":
            continue
        name = extract_subject(content)
        if name:
            return name, "recent_user"
        break

    return "", "none"


def _progress_marks(name: str, progress: Dict[str, Dict[str, bool]]) -> str:
    p = progress.get(name) or {}
    marks = []
    for step in _SUBSTEP_ORDER:
        label = {"character_design": "设", "look_design": "定", "character_card": "卡"}.get(step, "?")
        marks.append(f"{label}{'✓' if p.get(step) else '○'}")
    return "".join(marks)


def format_character_roster_block(stored: Dict[str, Any], *, active_name: str = "", substep: str = "") -> str:
    roster: List[str] = list(stored.get("character_roster") or [])
    progress: Dict[str, Dict[str, bool]] = stored.get("character_progress") or {}
    if not roster and not active_name:
        return ""

    lines = ["【角色设计队列 · 按顺序协作（高优先级）】"]
    if roster:
        parts = []
        for i, name in enumerate(roster, 1):
            tag = " ← 当前" if name == active_name else ""
            parts.append(f"{i}.{name}({_progress_marks(name, progress)}){tag}")
        lines.append("- **顺序队列**：" + " · ".join(parts))
        lines.append(
            "- 须**按队列顺序**逐位完成「宏观设计 → 定妆图 → 16:9 角色卡」；"
            "当前位未完成前，默认不跳到下一位（除非用户点名）。"
        )
    if active_name:
        sub_label = CHARACTER_SUBSTEPS.get(substep, substep) if substep else "（按对话推断子步骤）"
        lines.append(f"- **当前活跃角色**：{active_name} · 子步骤：{sub_label}")
        lines.append(
            f"- **禁止**因对话压缩/摘要缺失而声称「缺少{active_name}已确认设定」并擅自换角；"
            f"须从【对话摘要】/队列进度/本轮之前交付中继承{active_name}的已确认字段，"
            "不足处标 draft 并向用户列出待补项。"
        )
    else:
        lines.append("- 未能锁定活跃角色：请根据队列或上轮「下一步可选」确认，勿默认第一个历史角色。")
    return "\n".join(lines)
