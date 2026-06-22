"""创作阶段推断单元测试。"""
from app.core.drama.agent_stage_inference import infer_stage_from_message


def test_infer_character_from_role_image_request():
    msg = "我计划给沈砚生设计角色图 按流程引导我下"
    assert infer_stage_from_message(msg, "production") == "character"


def test_infer_character_from_design_keywords():
    assert infer_stage_from_message("帮我做角色定妆", "concept") == "character"


def test_no_switch_when_already_character():
    assert infer_stage_from_message("继续完善角色卡", "character") is None


def test_explicit_stage_mention():
    assert infer_stage_from_message("切换到角色阶段", "production") == "character"


def test_production_not_override_character_workflow():
    assert infer_stage_from_message("开始出图", "character") is None
