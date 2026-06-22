"""创作助手 · 绑定风格全生命周期锁定（仅用户显式取消可解除）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


@dataclass
class StyleSyncResult:
    effective_style_id: str
    persist_style_id: Optional[str]
    updated: bool
    locked: bool
    action: str  # noop | bind | change | keep_locked | ignore_clear

    def to_trace_detail(self) -> str:
        parts = [f"action={self.action}"]
        if self.effective_style_id:
            parts.append(f"style={self.effective_style_id}")
        if self.locked:
            parts.append("locked=true")
        return " · ".join(parts)


def _norm_style_id(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def resolve_thread_style_sync(
    thread: Dict[str, Any],
    *,
    sync_style: bool,
    incoming_style_id: Optional[str],
) -> StyleSyncResult:
    """
    解析 chat 请求中的风格同步。

    规则：
    - 线程已绑定风格 → 锁定；chat 传 null/空 **不会** 清除（防误传）
    - 线程已绑定 + chat 传不同非空 id → 允许更换（用户在选风格后发送）
    - 线程未绑定 + chat 传非空 id → 首次绑定并锁定
    - sync_style=False → 始终使用线程已有风格
    """
    locked_id = _norm_style_id(thread.get("style_preset_id"))
    incoming = _norm_style_id(incoming_style_id) if sync_style else None

    if not sync_style:
        return StyleSyncResult(
            effective_style_id=locked_id or "",
            persist_style_id=None,
            updated=False,
            locked=bool(locked_id),
            action="noop",
        )

    if locked_id:
        if incoming is None:
            return StyleSyncResult(
                effective_style_id=locked_id,
                persist_style_id=None,
                updated=False,
                locked=True,
                action="ignore_clear",
            )
        if incoming == locked_id:
            return StyleSyncResult(
                effective_style_id=locked_id,
                persist_style_id=None,
                updated=False,
                locked=True,
                action="keep_locked",
            )
        return StyleSyncResult(
            effective_style_id=incoming,
            persist_style_id=incoming,
            updated=True,
            locked=True,
            action="change",
        )

    if incoming:
        return StyleSyncResult(
            effective_style_id=incoming,
            persist_style_id=incoming,
            updated=True,
            locked=True,
            action="bind",
        )

    return StyleSyncResult(
        effective_style_id="",
        persist_style_id=None,
        updated=False,
        locked=False,
        action="noop",
    )


def format_style_lock_block(*, style_name: str, style_id: str) -> str:
    label = style_name or style_id
    return f"""【绑定视觉风格 · 全对话锁定（高优先级）】
风格：{label}（{style_id}）
说明：本对话自用户选定该风格起已锁定；创意脑暴、角色、场景、分镜中的 **所有视觉描述** 须与 style_analysis / render_class 一致。
**禁止**擅自切换、混搭其他画风或写实/3D/水墨等其他 render_class；**禁止**因用户未提及风格而改用默认风格。
仅当用户通过界面 **取消绑定风格** 后，才可视为无绑定风格。"""
