"""创作助手 ↔ 画布绑定（防递归）。"""
import asyncio
from unittest.mock import AsyncMock, patch

from app.services.drama_agent_thread_service import DramaAgentThreadService


def test_bind_canvas_no_recursion_when_canvas_has_agent_thread_id():
    svc = DramaAgentThreadService()

    thread_doc = {
        "thread_id": "dat_abc",
        "canvas_project_id": None,
        "status": "active",
        "_id": "1",
    }

    async def find_one(query, *args, **kwargs):
        if query.get("thread_id") == "dat_abc":
            return dict(thread_doc)
        if query.get("canvas_project_id") == "cp_new":
            return None
        return None

    mock_threads = AsyncMock()
    mock_threads.find_one = find_one
    mock_threads.update_one = AsyncMock()
    svc._threads = mock_threads

    canvas_svc = AsyncMock()
    canvas_svc.bind_agent_thread = AsyncMock(return_value={"project_id": "cp_new"})

    with patch(
        "app.services.canvas_service.get_canvas_service",
        return_value=canvas_svc,
    ):
        result = asyncio.run(svc.bind_canvas("dat_abc", "cp_new"))

    assert result["canvas_project_id"] == "cp_new"
    mock_threads.update_one.assert_awaited_once()
    canvas_svc.bind_agent_thread.assert_awaited_once_with("cp_new", "dat_abc")


def test_resolve_canvas_binding_direct_update():
    svc = DramaAgentThreadService()
    thread = {"thread_id": "dat_abc", "canvas_project_id": ""}

    canvas_svc = AsyncMock()
    canvas_svc.get_project_by_agent_thread = AsyncMock(
        return_value={"project_id": "cp_from_canvas", "agent_thread_id": "dat_abc"}
    )
    mock_threads = AsyncMock()
    mock_threads.update_one = AsyncMock()
    svc._threads = mock_threads

    with patch(
        "app.services.canvas_service.get_canvas_service",
        return_value=canvas_svc,
    ):
        out = asyncio.run(svc._resolve_canvas_binding(thread))

    assert out["canvas_project_id"] == "cp_from_canvas"
    mock_threads.update_one.assert_awaited_once()
