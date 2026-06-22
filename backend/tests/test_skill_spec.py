"""Skill 标准规范单元测试。"""
from pathlib import Path

from app.core.drama.skill_spec import (
    enrich_skill_payload,
    load_repo_skill,
    parse_frontmatter,
    scan_repo_skill_folders,
    skill_spec_template,
    validate_skill_content,
)


def test_parse_frontmatter():
    text = skill_spec_template(skill_name="测试", skill_id="skill.test")
    meta, body = parse_frontmatter(text)
    assert meta["skill_id"] == "skill.test"
    assert "一、技能简介" in body


def test_validate_skill_content():
    text = skill_spec_template(skill_id="skill.demo", skill_name="Demo")
    validate_skill_content(text, skill_code="skill.demo")


def test_enrich_skill_payload():
    text = skill_spec_template(skill_id="skill.demo", skill_name="Demo Skill", tag="test/tag")
    out = enrich_skill_payload({"skill_code": "skill.demo", "skill_content_md": text})
    assert out["name"] == "Demo Skill"
    assert out["system_markdown"]
    assert out["skill_meta"]["skill_id"] == "skill.demo"


def test_scan_repo_skill_folders():
    root = Path(__file__).resolve().parents[2] / "skills"
    items = scan_repo_skill_folders(root)
    folders = [i["folder"] for i in items]
    assert "skill_art_tianshuqitan" in folders
    assert "skill_character" in folders


def test_load_repo_skill():
    root = Path(__file__).resolve().parents[2] / "skills"
    payload = load_repo_skill("skill_art_tianshuqitan", root=root)
    assert payload["skill_code"] == "skill_art_tianshuqitan"
    assert payload["source_type"] == "repo"
    assert payload["skill_content_md"]


def test_load_repo_skill_character():
    root = Path(__file__).resolve().parents[2] / "skills"
    payload = load_repo_skill("skill_character", root=root)
    assert payload["skill_code"] == "skill.character"
    assert "16:9" in payload["skill_content_md"]
    assert "card_dimensions" in payload["skill_content_md"]


def test_load_repo_skill_scene():
    root = Path(__file__).resolve().parents[2] / "skills"
    payload = load_repo_skill("skill_scene", root=root)
    assert payload["skill_code"] == "skill.scene"
    assert "scene_inventory" in payload["skill_content_md"]
    assert "scene-prompt" in payload["skill_content_md"]
    assert "scene-grid-prompt" in payload["skill_content_md"]
    assert "scene_grid_6" in payload["skill_content_md"]


def test_load_repo_skill_storyboard():
    root = Path(__file__).resolve().parents[2] / "skills"
    payload = load_repo_skill("skill_storyboard", root=root)
    assert payload["skill_code"] == "skill.storyboard"
    assert "shot_list" in payload["skill_content_md"]
    assert "visual_description_zh" in payload["skill_content_md"]
    assert "camera_defaults" in payload["skill_content_md"]


def test_load_repo_skill_production():
    root = Path(__file__).resolve().parents[2] / "skills"
    payload = load_repo_skill("skill_production", root=root)
    assert payload["skill_code"] == "skill.production"
    assert "production-tasks" in payload["skill_content_md"]
    assert "image-prompt" in payload["skill_content_md"]
    assert "video-prompt" in payload["skill_content_md"]
