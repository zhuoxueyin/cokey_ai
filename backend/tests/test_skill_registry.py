"""Skill 注册表：创作助手仅允许 Skill 库已发布 Skill。"""
import pytest
from unittest.mock import AsyncMock, patch

from app.core.drama.skill_registry import (
    STAGE_SKILL_MAP,
    SkillNotRegisteredError,
    format_skill_for_agent_prompt,
    format_skill_hint_json,
    get_registered_skill,
    require_registered_skill,
    resolve_stage_skill,
)


@pytest.mark.asyncio
async def test_get_registered_skill_delegates_to_service():
    mock_svc = AsyncMock()
    mock_svc.get_published = AsyncMock(return_value={"skill_code": "skill.concept", "name": "创意"})
    with patch(
        "app.services.drama_skill_service.get_drama_skill_service",
        return_value=mock_svc,
    ):
        doc = await get_registered_skill("skill.concept")
    assert doc["skill_code"] == "skill.concept"
    mock_svc.get_published.assert_awaited_once_with("skill.concept")


@pytest.mark.asyncio
async def test_require_registered_skill_raises_when_missing():
    with patch(
        "app.core.drama.skill_registry.get_registered_skill",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(SkillNotRegisteredError) as exc:
            await require_registered_skill("skill.character", stage="character")
    assert exc.value.skill_code == "skill.character"
    assert exc.value.stage == "character"
    assert "Skill 库" in str(exc.value)


@pytest.mark.asyncio
async def test_resolve_stage_skill_no_mapping():
    code, doc = await resolve_stage_skill("unknown_stage", required=True)
    assert code is None
    assert doc is None


@pytest.mark.asyncio
async def test_resolve_stage_skill_production_maps_to_skill():
    with patch(
        "app.core.drama.skill_registry.get_registered_skill",
        new=AsyncMock(return_value={"skill_code": "skill.production", "name": "生产"}),
    ):
        code, doc = await resolve_stage_skill("production", required=True)
    assert code == "skill.production"
    assert doc["name"] == "生产"


@pytest.mark.asyncio
async def test_resolve_stage_skill_required_raises():
    with patch(
        "app.core.drama.skill_registry.get_registered_skill",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(SkillNotRegisteredError):
            await resolve_stage_skill("concept", required=True)
    assert STAGE_SKILL_MAP["concept"] == "skill.concept"


def test_format_skill_for_agent_prompt():
    text = format_skill_for_agent_prompt(
        {
            "skill_code": "skill.concept",
            "name": "创意策划",
            "version": "1.0.0",
            "source_type": "online",
            "skill_content_md": "## 技能简介\n测试正文",
        }
    )
    assert "Skill 库已注册" in text
    assert "skill.concept" in text
    assert "测试正文" in text
    assert "覆盖旧版" in text


def test_format_skill_hint_json():
    import json

    raw = format_skill_hint_json(
        {"name": "创意", "stage": "concept", "skill_content_md": "x" * 3000},
        "skill.concept",
    )
    obj = json.loads(raw)
    assert obj["registered"] is True
    assert obj["skill_code"] == "skill.concept"
    assert len(obj["content_preview"]) <= 2000
