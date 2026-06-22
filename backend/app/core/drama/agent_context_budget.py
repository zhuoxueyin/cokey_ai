"""创作助手上下文预算 — 分层裁剪（借鉴 Claude Code 渐进式 compaction 思路）。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

# 近似字符预算（~4 字/token）；128k 模型可用更高，默认保守
DEFAULT_CHAR_BUDGET = 48_000
RESERVE_FOR_USER_AND_REPLY = 6_000

LAYER_CAPS: Dict[str, int] = {
    "system_core": 4_000,
    "skill": 12_000,
    "style": 5_000,
    "project_memory": 3_000,
    "thread_summary": 2_500,
    "system_reminders": 800,
    "knowledge": 2_000,
    "tools": 4_000,
    "character_style": 2_500,
    "history": 18_000,
    "refs": 1_200,
}


@dataclass
class BudgetReport:
    total_budget: int
    used: int = 0
    layers: Dict[str, int] = field(default_factory=dict)
    actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_budget": self.total_budget,
            "used": self.used,
            "layers": dict(self.layers),
            "actions": list(self.actions),
        }


def snip_text(text: str, max_chars: int, *, suffix: str = "…") -> Tuple[str, bool]:
    t = (text or "").strip()
    if max_chars <= 0:
        return "", bool(t)
    if len(t) <= max_chars:
        return t, False
    cut = max(0, max_chars - len(suffix))
    return t[:cut].rstrip() + suffix, True


def snip_history_turn(content: str, max_chars: int) -> Tuple[str, bool]:
    """Snip：单条历史消息裁剪（最廉价层）。"""
    return snip_text(content, max_chars)


def trim_layer(name: str, text: str, cap: int, report: BudgetReport) -> str:
    trimmed, did = snip_text(text, cap)
    report.layers[name] = len(trimmed)
    report.used += len(trimmed)
    if did:
        report.actions.append(f"budget_trim:{name}")
    return trimmed


def apply_history_budget(
    turns: List[Tuple[str, str]],
    *,
    max_turns: int,
    max_per_turn: int,
    total_cap: int,
) -> Tuple[str, List[Tuple[str, str]], BudgetReport]:
    """Microcompact：限制轮数 + 单条长度 + 历史总字符上限。"""
    report = BudgetReport(total_budget=total_cap)
    recent = turns[-max_turns:] if max_turns > 0 else []
    lines: List[str] = []
    used = 0
    for role, content in recent:
        clipped, did = snip_history_turn(content, max_per_turn)
        if did:
            report.actions.append("snip:history_turn")
        line = f"{'用户' if role == 'user' else '助手'}: {clipped}"
        if used + len(line) + 1 > total_cap:
            report.actions.append("microcompact:history_total_cap")
            break
        lines.append(line)
        used += len(line) + 1
    report.used = used
    report.layers["history"] = used
    return "\n".join(lines), recent, report


def build_system_reminders(
    *,
    stage: str,
    agent_mode_name: str,
    style_name: str | None,
    style_id: str | None,
    ref_count: int,
    message_count: int,
    compact_summary_present: bool,
    compact_covers_through: int | None = None,
    active_character: str | None = None,
    character_substep: str | None = None,
) -> str:
    """每轮重注入 volatile 状态（类似 Claude Code system reminders）。"""
    lines = [
        "【系统提醒 · 实时状态】",
        f"- 创作类型：{agent_mode_name}",
        f"- 当前阶段：{stage}（全对话须遵循该阶段 Skill 与输出范式）",
    ]
    if style_id:
        label = style_name or style_id
        lines.append(f"- 绑定风格：{label}（{style_id}）· **全对话锁定**，不得切换或混搭其他画风")
    else:
        lines.append("- 绑定风格：未选择（用户选定后将全对话锁定）")
    if ref_count:
        lines.append(f"- 本轮 @ 引用：{ref_count} 项（含 vision 多模态）")
    if stage == "character" and active_character:
        from app.core.drama.agent_character_focus import CHARACTER_SUBSTEPS

        sub_label = CHARACTER_SUBSTEPS.get(character_substep or "", character_substep or "—")
        lines.append(f"- 活跃角色：{active_character}（子步骤：{sub_label}）")
    if compact_summary_present:
        thru = compact_covers_through or 0
        lines.append(f"- 对话轮次：{message_count}；早期约 {thru} 条已压缩为摘要（见【对话摘要】）")
    else:
        lines.append(f"- 对话轮次：{message_count}")
    lines.append("- 须区分 draft 与可确认设定；可确认项请明确标注供后续锁定。")
    return "\n".join(lines)
