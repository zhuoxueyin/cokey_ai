"""创作助手上下文预算与记忆单元测试。"""
from app.core.drama.agent_context_budget import (
    apply_history_budget,
    build_system_reminders,
    snip_text,
)


def test_snip_text():
    out, did = snip_text("hello world", 8)
    assert did
    assert len(out) <= 8


def test_apply_history_budget_total_cap():
    turns = [("user", "a" * 500)] * 10
    text, _, report = apply_history_budget(
        turns, max_turns=10, max_per_turn=200, total_cap=800
    )
    assert len(text) <= 800
    assert "microcompact" in " ".join(report.actions) or "snip" in " ".join(report.actions)


def test_build_system_reminders_with_summary():
    block = build_system_reminders(
        stage="character",
        agent_mode_name="AIGC漫剧",
        style_name="上美画风",
        style_id="american_boom_era",
        ref_count=2,
        message_count=24,
        compact_summary_present=True,
        compact_covers_through=12,
    )
    assert "american_boom_era" in block
    assert "已压缩" in block
