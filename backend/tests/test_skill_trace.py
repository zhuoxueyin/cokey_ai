"""Skill trace 步骤单元测试。"""
from app.core.drama.skill_registry import (
    PRODUCTION_SKILL_SKIP_SUMMARY,
    skill_trace_for_stage,
)


def test_skill_trace_production_single_skip():
    step = skill_trace_for_stage("production", None, None)
    assert step["step_id"] == "skill_load"
    assert step["status"] == "skip"
    assert step["summary"] == PRODUCTION_SKILL_SKIP_SUMMARY
    assert "无限画布" in step["detail"]


def test_skill_trace_with_registered_skill():
    step = skill_trace_for_stage(
        "concept",
        "skill.concept",
        {"name": "创意策划", "skill_code": "skill.concept", "skill_content_md": "## test"},
    )
    assert step["status"] == "ok"
    assert "skill.concept" in step["summary"]
