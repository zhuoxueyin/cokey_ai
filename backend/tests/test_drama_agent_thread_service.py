"""创作助手线程 update_thread 行为。"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.drama_agent_thread_service import DramaAgentThreadService


@pytest.mark.asyncio
async def test_update_thread_allows_style_change_after_messages():
    svc = DramaAgentThreadService()
    messages = AsyncMock()
    messages.count_documents = AsyncMock(return_value=3)
    threads = AsyncMock()
    threads.update_one = AsyncMock()
    svc._messages = messages
    svc._threads = threads

    updated_doc = {
        "_id": "oid",
        "thread_id": "dat_test",
        "style_preset_id": "american_boom_era",
        "agent_mode": "aigc_manga",
        "created_at": __import__("datetime").datetime.utcnow(),
        "updated_at": __import__("datetime").datetime.utcnow(),
    }
    svc.get_thread = AsyncMock(return_value=svc._ser(updated_doc))

    result = await svc.update_thread(
        "dat_test",
        {"style_preset_id": "american_boom_era", "agent_mode": "creative_short_drama"},
    )

    messages.count_documents.assert_awaited_once_with({"thread_id": "dat_test"})
    threads.update_one.assert_awaited_once()
    payload = threads.update_one.await_args.args[1]["$set"]
    assert payload["style_preset_id"] == "american_boom_era"
    assert "agent_mode" not in payload
    assert result["style_preset_id"] == "american_boom_era"


@pytest.mark.asyncio
async def test_update_thread_can_clear_style_preset_id():
    svc = DramaAgentThreadService()
    messages = AsyncMock()
    messages.count_documents = AsyncMock(return_value=1)
    threads = AsyncMock()
    threads.update_one = AsyncMock()
    svc._messages = messages
    svc._threads = threads

    cleared_doc = {
        "_id": "oid",
        "thread_id": "dat_test",
        "style_preset_id": None,
        "agent_mode": "aigc_manga",
        "created_at": __import__("datetime").datetime.utcnow(),
        "updated_at": __import__("datetime").datetime.utcnow(),
    }
    svc.get_thread = AsyncMock(return_value=svc._ser(cleared_doc))

    await svc.update_thread("dat_test", {"style_preset_id": None})

    payload = threads.update_one.await_args.args[1]["$set"]
    assert "style_preset_id" in payload
    assert payload["style_preset_id"] is None
