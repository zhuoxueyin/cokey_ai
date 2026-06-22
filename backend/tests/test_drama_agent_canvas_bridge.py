"""创作助手 → 画布绑定。"""
import pytest
from unittest.mock import AsyncMock, patch

from app.services.drama_agent_canvas_bridge import spawn_canvas_from_agent_thread


@pytest.mark.asyncio
async def test_spawn_canvas_idempotent_when_already_bound():
    thread_svc = AsyncMock()
    canvas_svc = AsyncMock()

    thread_svc.get_thread.return_value = {
        "thread_id": "dat_abc",
        "title": "测试短剧",
        "canvas_project_id": "cp_existing",
    }
    canvas_svc.get_project.return_value = {"project_id": "cp_existing", "title": "已有画布"}

    with patch(
        "app.services.drama_agent_canvas_bridge.get_drama_agent_thread_service",
        return_value=thread_svc,
    ), patch(
        "app.services.drama_agent_canvas_bridge.get_canvas_service",
        return_value=canvas_svc,
    ):
        result = await spawn_canvas_from_agent_thread("dat_abc")

    assert result["project_id"] == "cp_existing"
    assert result["already_bound"] is True
    assert result["seed_node_ids"] == []
    canvas_svc.create_project.assert_not_called()


@pytest.mark.asyncio
async def test_spawn_canvas_repairs_binding_from_reverse_lookup():
    thread_svc = AsyncMock()
    canvas_svc = AsyncMock()

    thread_svc.get_thread.return_value = {
        "thread_id": "dat_abc",
        "title": "测试短剧",
    }
    canvas_svc.get_project_by_agent_thread.return_value = {
        "project_id": "cp_from_canvas",
        "title": "已有画布",
        "agent_thread_id": "dat_abc",
    }
    thread_svc.bind_canvas.return_value = {
        "thread_id": "dat_abc",
        "canvas_project_id": "cp_from_canvas",
    }

    with patch(
        "app.services.drama_agent_canvas_bridge.get_drama_agent_thread_service",
        return_value=thread_svc,
    ), patch(
        "app.services.drama_agent_canvas_bridge.get_canvas_service",
        return_value=canvas_svc,
    ):
        result = await spawn_canvas_from_agent_thread("dat_abc")

    assert result["project_id"] == "cp_from_canvas"
    assert result["already_bound"] is True
    assert result["binding_repaired"] is True
    canvas_svc.create_project.assert_not_called()
    thread_svc.bind_canvas.assert_called_once_with("dat_abc", "cp_from_canvas")


@pytest.mark.asyncio
async def test_spawn_canvas_clears_stale_binding_and_reverse_lookup():
    thread_svc = AsyncMock()
    canvas_svc = AsyncMock()

    thread_svc.get_thread.return_value = {
        "thread_id": "dat_stale",
        "title": "旧绑定",
        "canvas_project_id": "cp_deleted",
    }
    canvas_svc.get_project.return_value = None
    canvas_svc.get_project_by_agent_thread.return_value = {
        "project_id": "cp_real",
        "agent_thread_id": "dat_stale",
    }
    thread_svc.bind_canvas.return_value = {
        "thread_id": "dat_stale",
        "canvas_project_id": "cp_real",
    }

    with patch(
        "app.services.drama_agent_canvas_bridge.get_drama_agent_thread_service",
        return_value=thread_svc,
    ), patch(
        "app.services.drama_agent_canvas_bridge.get_canvas_service",
        return_value=canvas_svc,
    ):
        result = await spawn_canvas_from_agent_thread("dat_stale")

    assert result["project_id"] == "cp_real"
    assert result["binding_repaired"] is True
    thread_svc.update_thread.assert_called_once_with("dat_stale", {"canvas_project_id": None})
    canvas_svc.create_project.assert_not_called()


@pytest.mark.asyncio
async def test_spawn_canvas_creates_project_and_binds_without_seed_nodes():
    thread_svc = AsyncMock()
    canvas_svc = AsyncMock()

    thread_svc.get_thread.return_value = {
        "thread_id": "dat_new",
        "title": "新剧本",
        "agent_mode": "creative_short_drama",
        "stage": "script",
        "user_id": "u1",
    }
    canvas_svc.get_project_by_agent_thread.return_value = None
    canvas_svc.create_project.return_value = {"project_id": "cp_new", "title": "新剧本 · 画布"}
    thread_svc.bind_canvas.return_value = {"thread_id": "dat_new", "canvas_project_id": "cp_new"}

    with patch(
        "app.services.drama_agent_canvas_bridge.get_drama_agent_thread_service",
        return_value=thread_svc,
    ), patch(
        "app.services.drama_agent_canvas_bridge.get_canvas_service",
        return_value=canvas_svc,
    ):
        result = await spawn_canvas_from_agent_thread("dat_new", user_id="u1")

    assert result["project_id"] == "cp_new"
    assert result["already_bound"] is False
    assert result["seed_node_ids"] == []
    canvas_svc.create_project.assert_called_once()
    thread_svc.bind_canvas.assert_called_once_with("dat_new", "cp_new")
    canvas_svc.create_node.assert_not_called()
    canvas_svc.create_edge.assert_not_called()
    thread_svc.list_messages.assert_not_called()
    thread_svc.update_thread.assert_not_called()
