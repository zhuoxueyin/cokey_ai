"""Skill 正文对比（发布前 diff）。"""
from __future__ import annotations

import difflib
from typing import Any, Dict


def compare_skill_texts(
    old: str,
    new: str,
    *,
    from_label: str = "线上已发布",
    to_label: str = "待发布草稿",
) -> Dict[str, Any]:
    old_text = old or ""
    new_text = new or ""
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    unified = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=from_label,
        tofile=to_label,
        lineterm="",
    )
    return {
        "has_changes": old_text.strip() != new_text.strip(),
        "unified_diff": "\n".join(unified),
        "old_line_count": len(old_lines),
        "new_line_count": len(new_lines),
    }
