"""创作助手 · 风格全对话锁定。"""
from app.core.drama.agent_style_lock import resolve_thread_style_sync


def test_locked_style_ignores_null_clear_on_chat():
    thread = {"thread_id": "t1", "style_preset_id": "shangmei"}
    result = resolve_thread_style_sync(thread, sync_style=True, incoming_style_id=None)
    assert result.action == "ignore_clear"
    assert result.effective_style_id == "shangmei"
    assert not result.updated
    assert result.locked


def test_first_bind_on_chat():
    thread = {"thread_id": "t1", "style_preset_id": None}
    result = resolve_thread_style_sync(thread, sync_style=True, incoming_style_id="shangmei")
    assert result.action == "bind"
    assert result.persist_style_id == "shangmei"
    assert result.updated


def test_no_sync_uses_thread_style():
    thread = {"thread_id": "t1", "style_preset_id": "shangmei"}
    result = resolve_thread_style_sync(thread, sync_style=False, incoming_style_id=None)
    assert result.action == "noop"
    assert result.effective_style_id == "shangmei"


def test_locked_style_allows_change():
    thread = {"thread_id": "t1", "style_preset_id": "shangmei"}
    result = resolve_thread_style_sync(
        thread, sync_style=True, incoming_style_id="american_boom_era"
    )
    assert result.action == "change"
    assert result.persist_style_id == "american_boom_era"
    assert result.updated
