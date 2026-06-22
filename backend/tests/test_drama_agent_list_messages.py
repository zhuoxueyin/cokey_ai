"""创作助手消息列表应返回最近 N 条，而非最早 N 条。"""
from datetime import datetime, timedelta

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.drama_agent_thread_service import DramaAgentThreadService


def _msg(message_id: str, created_at: datetime) -> dict:
    return {
        "_id": message_id,
        "message_id": message_id,
        "thread_id": "dat_test",
        "role": "user",
        "content": message_id,
        "refs": [],
        "meta": {},
        "created_at": created_at,
    }


@pytest.mark.asyncio
async def test_list_messages_tail_returns_latest():
    svc = DramaAgentThreadService()
    base = datetime.utcnow()
    docs = [_msg(f"msg_{i}", base + timedelta(seconds=i)) for i in range(5)]

    class _Cursor:
        def __init__(self, items):
            self._items = items

        def sort(self, key, direction):
            reverse = direction == -1
            self._items = sorted(self._items, key=lambda d: d["created_at"], reverse=reverse)
            return self

        def limit(self, n):
            self._items = self._items[:n]
            return self

        def __aiter__(self):
            self._iter = iter(self._items)
            return self

        async def __anext__(self):
            try:
                return next(self._iter)
            except StopIteration:
                raise StopAsyncIteration

    messages = MagicMock()
    messages.find = MagicMock(return_value=_Cursor(list(docs)))
    svc._messages = messages

    result = await svc.list_messages("dat_test", limit=3, tail=True)

    assert [m["message_id"] for m in result] == ["msg_2", "msg_3", "msg_4"]


@pytest.mark.asyncio
async def test_list_messages_head_returns_earliest_when_tail_false():
    svc = DramaAgentThreadService()
    base = datetime.utcnow()
    docs = [_msg(f"msg_{i}", base + timedelta(seconds=i)) for i in range(5)]

    class _Cursor:
        def __init__(self, items):
            self._items = items

        def sort(self, key, direction):
            reverse = direction == -1
            self._items = sorted(self._items, key=lambda d: d["created_at"], reverse=reverse)
            return self

        def limit(self, n):
            self._items = self._items[:n]
            return self

        def __aiter__(self):
            self._iter = iter(self._items)
            return self

        async def __anext__(self):
            try:
                return next(self._iter)
            except StopIteration:
                raise StopAsyncIteration

    messages = MagicMock()
    messages.find = MagicMock(return_value=_Cursor(list(docs)))
    svc._messages = messages

    result = await svc.list_messages("dat_test", limit=3, tail=False)

    assert [m["message_id"] for m in result] == ["msg_0", "msg_1", "msg_2"]
