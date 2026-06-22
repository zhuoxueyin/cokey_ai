"""超级创意 Agent 单元测试。"""
from unittest.mock import AsyncMock, patch

import pytest

from app.core.drama.agent_tools import prefetch_tool_context, search_knowledge_tool
from app.core.drama.skill_registry import SkillNotRegisteredError
from app.services.drama_super_agent_service import SuperCreativeAgent


_MOCK_SKILL = {
    "skill_code": "skill.concept",
    "name": "创意策划",
    "version": "1.0.0",
    "source_type": "online",
    "skill_content_md": "## 测试 Skill",
}


def _patch_registered_skill():
    return patch(
        "app.services.drama_super_agent_service.resolve_stage_skill",
        new=AsyncMock(return_value=("skill.concept", _MOCK_SKILL)),
    )


def _patch_task_service():
    task_svc = AsyncMock()
    task_svc.create = AsyncMock(
        return_value={"task_id": "task_test", "trace_id": "trace_test"},
    )
    task_svc.update_status = AsyncMock(return_value=True)
    return patch(
        "app.services.drama_super_agent_service.get_task_service",
        return_value=task_svc,
    )


@pytest.mark.asyncio
async def test_search_knowledge_tool_empty():
    with patch(
        "app.services.drama_knowledge_service.get_drama_knowledge_service"
    ) as mock_get:
        svc = AsyncMock()
        svc.search = AsyncMock(return_value=[])
        mock_get.return_value = svc
        out = await search_knowledge_tool("测试", categories=["short_drama"])
        assert "未找到" in out


@pytest.mark.asyncio
async def test_super_agent_chat_mock_gateway():
    thread_svc = AsyncMock()
    thread_svc.get_thread = AsyncMock(
        return_value={
            "thread_id": "dat_test",
            "agent_mode": "creative_short_drama",
            "stage": "concept",
            "model_code": "text_model",
        }
    )
    thread_svc.append_message = AsyncMock(
        side_effect=lambda tid, role, content, **kw: {
            "message_id": f"msg_{role}",
            "role": role,
            "content": content,
        }
    )
    thread_svc.get_recent_for_prompt = AsyncMock(return_value=[])
    thread_svc.list_messages = AsyncMock(return_value=[])

    knowledge_svc = AsyncMock()
    knowledge_svc.search = AsyncMock(return_value=[])

    gateway = AsyncMock()
    gateway.execute = AsyncMock(
        return_value={"success": True, "data": {"text": "你好，我是创意助手。"}}
    )

    with _patch_registered_skill(), _patch_task_service(), patch(
        "app.services.drama_super_agent_service.get_drama_agent_thread_service",
        return_value=thread_svc,
    ), patch(
        "app.services.drama_super_agent_service.get_drama_knowledge_service",
        return_value=knowledge_svc,
    ), patch(
        "app.services.drama_super_agent_service.prefetch_tool_context",
        new=AsyncMock(return_value={"prompt_block": "（无 Tool 命中）", "steps": []}),
    ), patch(
        "app.services.drama_super_agent_service.get_model_gateway",
        return_value=gateway,
    ), patch(
        "app.services.drama_super_agent_service.get_drama_style_service",
        return_value=AsyncMock(get_by_style_id=AsyncMock(return_value=None)),
    ):
        agent = SuperCreativeAgent()
        result = await agent.chat("dat_test", "写一个重生短剧创意")

    assert result["reply_markdown"] == "你好，我是创意助手。"
    assert result["thread_id"] == "dat_test"
    assert "process_trace" in result
    assert any(s["kind"] == "context" for s in result["process_trace"])
    gateway.execute.assert_awaited_once()
    call_kwargs = gateway.execute.await_args.kwargs
    assert call_kwargs["model_code"] == "text_model"
    assert call_kwargs["category"] == "text"
    assert call_kwargs["task_id"] == "task_test"
    assert call_kwargs["trace_id"] == "trace_test"


@pytest.mark.asyncio
async def test_super_agent_chat_strips_json_noise_on_concept_stage():
    thread_svc = AsyncMock()
    thread_svc.get_thread = AsyncMock(
        return_value={
            "thread_id": "dat_test",
            "agent_mode": "creative_short_drama",
            "stage": "concept",
            "model_code": "text_model",
        }
    )
    thread_svc.append_message = AsyncMock(
        side_effect=lambda tid, role, content, **kw: {
            "message_id": f"msg_{role}",
            "role": role,
            "content": content,
        }
    )
    thread_svc.get_recent_for_prompt = AsyncMock(return_value=[])
    thread_svc.list_messages = AsyncMock(return_value=[])

    mixed = (
        "## 剧本草稿\n主角重生归来，先隐忍再翻盘。\n\n"
        "```json\n"
        '{"theme":"复仇","tone":"爽感"}\n'
        "```\n\n"
        '{\n  "ideas": ["豪门博弈", "身份反转"]\n}\n\n'
        "## 选题方向\n- 豪门恩怨线\n- 女性成长线"
    )
    gateway = AsyncMock()
    gateway.execute = AsyncMock(return_value={"success": True, "data": {"text": mixed}})

    with _patch_registered_skill(), _patch_task_service(), patch(
        "app.services.drama_super_agent_service.get_drama_agent_thread_service",
        return_value=thread_svc,
    ), patch(
        "app.services.drama_super_agent_service.get_drama_knowledge_service",
        return_value=AsyncMock(search=AsyncMock(return_value=[])),
    ), patch(
        "app.services.drama_super_agent_service.prefetch_tool_context",
        new=AsyncMock(return_value={"prompt_block": "（无 Tool 命中）", "steps": []}),
    ), patch(
        "app.services.drama_super_agent_service.get_model_gateway",
        return_value=gateway,
    ), patch(
        "app.services.drama_super_agent_service.get_drama_style_service",
        return_value=AsyncMock(get_by_style_id=AsyncMock(return_value=None)),
    ):
        agent = SuperCreativeAgent()
        result = await agent.chat("dat_test", "给我三个脑暴方向")

    assert "```json" not in result["reply_markdown"]
    assert '"ideas"' not in result["reply_markdown"]
    assert "## 剧本草稿" in result["reply_markdown"]
    assert "## 选题方向" in result["reply_markdown"]


@pytest.mark.asyncio
async def test_super_agent_chat_syncs_style_preset_before_run():
    thread_svc = AsyncMock()
    thread_svc.get_thread = AsyncMock(
        side_effect=[
            {
                "thread_id": "dat_test",
                "agent_mode": "aigc_manga",
                "stage": "production",
                "model_code": "text_model",
                "style_preset_id": None,
            },
            {
                "thread_id": "dat_test",
                "agent_mode": "aigc_manga",
                "stage": "production",
                "model_code": "text_model",
                "style_preset_id": "american_boom_era",
            },
        ]
    )
    thread_svc.update_thread = AsyncMock(
        return_value={
            "thread_id": "dat_test",
            "agent_mode": "aigc_manga",
            "stage": "production",
            "model_code": "text_model",
            "style_preset_id": "american_boom_era",
        }
    )
    thread_svc.append_message = AsyncMock(return_value={"message_id": "msg_user"})
    thread_svc.get_recent_for_prompt = AsyncMock(return_value=[])
    thread_svc.list_messages = AsyncMock(return_value=[])

    prefetch = AsyncMock(return_value={"prompt_block": "（无 Tool 命中）", "steps": []})
    gateway = AsyncMock(
        return_value={"success": True, "data": {"text": "ok"}}
    )

    with _patch_registered_skill(), _patch_task_service(), patch(
        "app.services.drama_super_agent_service.get_drama_agent_thread_service",
        return_value=thread_svc,
    ), patch(
        "app.services.drama_super_agent_service.get_drama_knowledge_service",
        return_value=AsyncMock(search=AsyncMock(return_value=[])),
    ), patch(
        "app.services.drama_super_agent_service.prefetch_tool_context",
        new=prefetch,
    ), patch(
        "app.services.drama_super_agent_service.get_model_gateway",
        return_value=AsyncMock(execute=gateway),
    ), patch(
        "app.services.drama_super_agent_service.get_drama_style_service",
        return_value=AsyncMock(
            get_by_style_id=AsyncMock(
                return_value={
                    "style_id": "american_boom_era",
                    "name": "上美画风",
                    "model_prompts": {"style_summary_zh": "上美经典动画"},
                }
            )
        ),
    ):
        agent = SuperCreativeAgent()
        await agent.chat(
            "dat_test",
            "写分镜",
            style_preset_id="american_boom_era",
            sync_style=True,
        )

    thread_svc.update_thread.assert_awaited_once_with(
        "dat_test", {"style_preset_id": "american_boom_era"}
    )
    assert prefetch.await_args.kwargs.get("stage") == "production"


@pytest.mark.asyncio
async def test_super_agent_chat_skips_style_sync_when_disabled():
    thread_svc = AsyncMock()
    thread_svc.get_thread = AsyncMock(
        return_value={
            "thread_id": "dat_test",
            "agent_mode": "aigc_manga",
            "stage": "production",
            "model_code": "text_model",
            "style_preset_id": None,
        }
    )
    thread_svc.append_message = AsyncMock(return_value={"message_id": "msg_user"})
    thread_svc.get_recent_for_prompt = AsyncMock(return_value=[])
    thread_svc.list_messages = AsyncMock(return_value=[])

    prefetch = AsyncMock(return_value={"prompt_block": "（无 Tool 命中）", "steps": []})

    with _patch_registered_skill(), _patch_task_service(), patch(
        "app.services.drama_super_agent_service.get_drama_agent_thread_service",
        return_value=thread_svc,
    ), patch(
        "app.services.drama_super_agent_service.get_drama_knowledge_service",
        return_value=AsyncMock(search=AsyncMock(return_value=[])),
    ), patch(
        "app.services.drama_super_agent_service.prefetch_tool_context",
        new=prefetch,
    ), patch(
        "app.services.drama_super_agent_service.get_model_gateway",
        return_value=AsyncMock(
            execute=AsyncMock(return_value={"success": True, "data": {"text": "ok"}})
        ),
    ), patch(
        "app.services.drama_super_agent_service.get_drama_style_service",
        return_value=AsyncMock(get_by_style_id=AsyncMock(return_value=None)),
    ):
        agent = SuperCreativeAgent()
        await agent.chat("dat_test", "写分镜")

    thread_svc.update_thread.assert_not_called()
    assert prefetch.await_args.kwargs.get("stage") == "production"


@pytest.mark.asyncio
async def test_super_agent_chat_does_not_clear_locked_style_with_null():
    thread_svc = AsyncMock()
    thread_svc.get_thread = AsyncMock(
        return_value={
            "thread_id": "dat_test",
            "agent_mode": "aigc_manga",
            "stage": "character",
            "model_code": "text_model",
            "style_preset_id": "shangmei",
        }
    )
    thread_svc.append_message = AsyncMock(return_value={"message_id": "msg_user"})
    thread_svc.get_recent_for_prompt = AsyncMock(return_value=[])
    thread_svc.list_messages = AsyncMock(return_value=[])

    with _patch_registered_skill(), _patch_task_service(), patch(
        "app.services.drama_super_agent_service.get_drama_agent_thread_service",
        return_value=thread_svc,
    ), patch(
        "app.services.drama_super_agent_service.get_drama_knowledge_service",
        return_value=AsyncMock(search=AsyncMock(return_value=[])),
    ), patch(
        "app.services.drama_super_agent_service.prefetch_tool_context",
        new=AsyncMock(return_value={"prompt_block": "（无 Tool 命中）", "steps": []}),
    ), patch(
        "app.services.drama_super_agent_service.get_model_gateway",
        return_value=AsyncMock(
            execute=AsyncMock(return_value={"success": True, "data": {"text": "ok"}})
        ),
    ), patch(
        "app.services.drama_super_agent_service.get_drama_style_service",
        return_value=AsyncMock(
            get_by_style_id=AsyncMock(
                return_value={
                    "style_id": "shangmei",
                    "name": "上美画风",
                    "model_prompts": {"style_summary_zh": "上美经典动画"},
                }
            )
        ),
    ):
        agent = SuperCreativeAgent()
        await agent.chat(
            "dat_test",
            "定妆图设计",
            style_preset_id=None,
            sync_style=True,
        )

    thread_svc.update_thread.assert_not_called()


@pytest.mark.asyncio
async def test_super_agent_chat_includes_refs_in_prompt():
    thread_svc = AsyncMock()
    thread_svc.get_thread = AsyncMock(
        return_value={
            "thread_id": "dat_test",
            "agent_mode": "creative_short_drama",
            "stage": "concept",
            "model_code": "text_model",
        }
    )
    thread_svc.append_message = AsyncMock(
        side_effect=lambda tid, role, content, **kw: {
            "message_id": f"msg_{role}",
            "role": role,
            "content": content,
            "refs": kw.get("refs") or [],
        }
    )
    thread_svc.get_recent_for_prompt = AsyncMock(return_value=[])
    thread_svc.list_messages = AsyncMock(return_value=[])

    gateway = AsyncMock()
    gateway.execute = AsyncMock(return_value={"success": True, "data": {"text": "ok"}})

    refs = [{"type": "asset", "id": "asset_1", "url": "https://cdn.example.com/ref.jpg"}]

    with _patch_registered_skill(), _patch_task_service(), patch(
        "app.services.drama_super_agent_service.get_drama_agent_thread_service",
        return_value=thread_svc,
    ), patch(
        "app.services.drama_super_agent_service.get_drama_knowledge_service",
        return_value=AsyncMock(search=AsyncMock(return_value=[])),
    ), patch(
        "app.services.drama_super_agent_service.prefetch_tool_context",
        new=AsyncMock(return_value={"prompt_block": "（无 Tool 命中）", "steps": []}),
    ), patch(
        "app.services.drama_super_agent_service.get_model_gateway",
        return_value=gateway,
    ), patch(
        "app.services.drama_super_agent_service.get_drama_style_service",
        return_value=AsyncMock(get_by_style_id=AsyncMock(return_value=None)),
    ):
        agent = SuperCreativeAgent()
        result = await agent.chat("dat_test", "按这张图写分镜", refs=refs)

    prompt = gateway.execute.await_args.kwargs["params"]["prompt"]
    invoke_params = gateway.execute.await_args.kwargs["params"]
    assert "https://cdn.example.com/ref.jpg" in prompt
    assert invoke_params.get("images") == ["https://cdn.example.com/ref.jpg"]
    assert "用户 @ 引用资源" in prompt
    assert any(s.get("step_id") == "user_refs" for s in result["process_trace"])


@pytest.mark.asyncio
async def test_prefetch_tool_context_without_style():
    mock_skill = {
        "skill_code": "skill.concept",
        "name": "创意策划",
        "skill_content_md": "## 测试",
    }
    with patch(
        "app.core.drama.agent_tools.search_knowledge_tool",
        new=AsyncMock(return_value="- 条目1"),
    ), patch(
        "app.core.drama.agent_tools.require_registered_skill",
        new=AsyncMock(return_value=mock_skill),
    ):
        out = await prefetch_tool_context(
            message="创意",
            knowledge_categories=["short_drama"],
            stage="concept",
        )
    assert "search_knowledge" in out["prompt_block"]
    assert "resolve_style" not in out["prompt_block"]
    assert "invoke_skill_hint" not in out["prompt_block"]
    kinds = {s["kind"] for s in out["steps"]}
    assert "knowledge" in kinds
    assert "skill" not in kinds
    assert "style" not in kinds


@pytest.mark.asyncio
async def test_super_agent_chat_blocks_when_skill_not_registered():
    thread_svc = AsyncMock()
    thread_svc.get_thread = AsyncMock(
        return_value={
            "thread_id": "dat_test",
            "agent_mode": "creative_short_drama",
            "stage": "concept",
            "model_code": "text_model",
        }
    )
    thread_svc.append_message = AsyncMock(
        side_effect=lambda tid, role, content, **kw: {
            "message_id": f"msg_{role}",
            "role": role,
            "content": content,
        }
    )

    gateway = AsyncMock()

    with patch(
        "app.services.drama_super_agent_service.resolve_stage_skill",
        new=AsyncMock(
            side_effect=SkillNotRegisteredError("skill.concept", stage="concept")
        ),
    ), patch(
        "app.services.drama_super_agent_service.get_drama_agent_thread_service",
        return_value=thread_svc,
    ), patch(
        "app.services.drama_super_agent_service.get_model_gateway",
        return_value=gateway,
    ), patch(
        "app.services.drama_super_agent_service.get_drama_style_service",
        return_value=AsyncMock(get_by_style_id=AsyncMock(return_value=None)),
    ):
        agent = SuperCreativeAgent()
        result = await agent.chat("dat_test", "写一个创意")

    assert result["error"] is True
    assert result["error_code"] == "skill_not_registered"
    assert "Skill 库" in result["reply_markdown"]
    gateway.execute.assert_not_called()
