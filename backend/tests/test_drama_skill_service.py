"""Drama Skill 服务单元测试。"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.drama_skill_service import DramaSkillService


def test_repo_payload_unchanged_detects_content_diff():
    svc = DramaSkillService()
    existing = {"skill_content_md": "# a", "script_files": ["x.py"]}
    payload = {"skill_content_md": "# b", "script_files": ["x.py"]}
    assert svc._repo_payload_unchanged(existing, payload) is False


def test_compute_repo_sync_meta_no_repo_folder():
    svc = DramaSkillService()
    meta = svc.compute_repo_sync_meta({"skill_code": "skill.unknown"})
    assert meta["repo_available"] is False
    assert meta["repo_has_changes"] is False


def test_compute_repo_sync_meta_detects_repo_changes():
    svc = DramaSkillService()
    draft = {
        "skill_code": "skill.concept",
        "repo_path": "skill_concept",
        "skill_content_md": "---\nversion: 2.0.0\n---\n# old",
        "script_files": [],
    }
    repo_payload = {
        "skill_content_md": "---\nversion: 2.1.0\n---\n# new",
        "script_files": [],
    }
    meta = svc.compute_repo_sync_meta(draft, repo_payload=repo_payload)
    assert meta["repo_available"] is True
    assert meta["repo_has_changes"] is True
    assert meta["repo_version"] == "2.1.0"


def test_compute_repo_sync_meta_aligned():
    svc = DramaSkillService()
    content = "---\nversion: 2.1.0\n---\n# same"
    draft = {
        "skill_code": "skill.concept",
        "repo_path": "skill_concept",
        "skill_content_md": content,
        "script_files": [],
    }
    repo_payload = {"skill_content_md": content, "script_files": []}
    meta = svc.compute_repo_sync_meta(draft, repo_payload=repo_payload)
    assert meta["repo_has_changes"] is False


def test_infer_stage_for_skill_from_map():
    svc = DramaSkillService()
    assert svc._infer_stage_for_skill({"skill_code": "skill.character"}, "production") == "character"
    assert svc._infer_stage_for_skill({"skill_code": "skill.character"}, "outline") == "outline"
    assert svc._infer_stage_for_skill({"skill_code": "skill.unknown"}, "production") == "production"


@pytest.mark.asyncio
async def test_repo_sync_state_needs_publish_when_draft_matches_repo_not_published():
    svc = DramaSkillService()
    content_v41 = "---\nversion: 4.1.0\nskill_id: skill.character\n---\n# body v41"
    content_v40 = "---\nversion: 4.0.0\nskill_id: skill.character\n---\n# body v40"
    existing = {
        "skill_code": "skill.character",
        "version": "5.0.0",
        "status": "draft",
        "skill_content_md": content_v41,
    }
    payload = {"skill_content_md": content_v41, "script_files": []}
    published = {"skill_code": "skill.character", "version": "4.0.0", "skill_content_md": content_v40}

    with patch.object(svc, "get_published", new=AsyncMock(return_value=published)):
        sync = await svc._repo_sync_state(existing, payload)

    assert sync["unchanged"] is True
    assert sync["needs_publish"] is True
    assert sync["repo_version"] == "4.1.0"
    assert sync["published_version"] == "4.0.0"


@pytest.mark.asyncio
async def test_repo_sync_state_no_publish_when_all_aligned():
    svc = DramaSkillService()
    content = "---\nversion: 4.1.0\nskill_id: skill.character\n---\n# same"
    existing = {"skill_code": "skill.character", "version": "4.0.0", "status": "published", "skill_content_md": content}
    payload = {"skill_content_md": content, "script_files": []}
    published = {"skill_code": "skill.character", "version": "4.0.0", "skill_content_md": content}

    with patch.object(svc, "get_published", new=AsyncMock(return_value=published)):
        sync = await svc._repo_sync_state(existing, payload)

    assert sync["unchanged"] is True
    assert sync["needs_publish"] is False


@pytest.mark.asyncio
async def test_create_increments_version_num_when_latest_exists():
    svc = DramaSkillService()
    mock_collection = AsyncMock()
    mock_collection.find_one = AsyncMock(
        return_value={"skill_code": "skill.character", "version": "1.0.0", "version_num": 1}
    )
    inserted = {}

    async def _insert_one(doc):
        inserted.update(doc)
        result = MagicMock()
        result.inserted_id = "oid123"
        return result

    mock_collection.insert_one = _insert_one
    svc._collection = mock_collection

    with patch("app.core.drama.skill_spec.enrich_skill_payload", side_effect=lambda d: d), patch(
        "app.core.drama.skill_spec.validate_skill_content"
    ):
        doc = await svc.create(
            {
                "skill_code": "skill.character",
                "name": "角色卡",
                "skill_content_md": "",
            }
        )

    assert inserted["version_num"] == 2
    assert inserted["version"] == "2.0.0"
    assert doc["version_num"] == 2


@pytest.mark.asyncio
async def test_rollback_republishes_target_version():
    svc = DramaSkillService()
    target_oid = "507f1f77bcf86cd799439011"
    target_doc = {
        "_id": target_oid,
        "skill_code": "skill.character",
        "version_num": 3,
        "status": "archived",
    }
    published = {"skill_code": "skill.character", "version_num": 5, "status": "published"}

    mock_collection = AsyncMock()
    mock_collection.find_one = AsyncMock(return_value=target_doc)
    mock_collection.update_many = AsyncMock()
    mock_collection.update_one = AsyncMock()
    svc._collection = mock_collection

    with patch.object(svc, "get_published", new=AsyncMock(return_value=published)), patch(
        "app.services.drama_skill_service.DramaSkillService._serialize",
        side_effect=lambda d: {**d, "id": str(d["_id"])},
    ):
        result = await svc.rollback("skill.character", 3)

    assert result["version_num"] == 3
    mock_collection.update_many.assert_awaited_once()
    mock_collection.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_rollback_noop_when_already_published():
    svc = DramaSkillService()
    target_doc = {
        "_id": "507f1f77bcf86cd799439011",
        "skill_code": "skill.character",
        "version_num": 3,
        "status": "published",
    }
    published = {"skill_code": "skill.character", "version_num": 3, "id": "507f1f77bcf86cd799439011"}

    mock_collection = AsyncMock()
    mock_collection.find_one = AsyncMock(return_value=target_doc)
    svc._collection = mock_collection

    with patch.object(svc, "get_published", new=AsyncMock(return_value=published)):
        result = await svc.rollback("skill.character", 3)

    assert result["version_num"] == 3
    mock_collection.update_many.assert_not_called()
