"""知识检索关键词、阶段过滤、向量相似度单元测试。"""
import asyncio
from unittest.mock import AsyncMock, patch

from app.core.drama.knowledge_keyword import extract_keywords, score_entry_keywords
from app.core.drama.knowledge_stage import category_applies_to_stage, validate_applicable_stages
from app.core.drama.agent_tools import search_knowledge_hits
from app.services.knowledge_vector_service import cosine_similarity, embed_text
from app.services.drama_knowledge_service import DramaKnowledgeService


def test_extract_keywords_limit():
    kws = extract_keywords("参考动画短片叙事节奏与角色设定", max_keywords=10)
    assert len(kws) <= 10
    assert any("动画" in k or "短片" in k for k in kws)


def test_score_entry_keywords_multi_field():
    doc = {
        "title": "动画短片节奏",
        "tags": ["叙事"],
        "summary": "参考案例",
        "content_markdown": "角色设定细节",
    }
    score = score_entry_keywords(doc, ["动画", "角色"])
    assert score > 0


def test_category_applies_to_stage():
    assert category_applies_to_stage({"applicable_stages": ["character"]}, "character")
    assert not category_applies_to_stage({"applicable_stages": ["character"]}, "script")
    assert category_applies_to_stage({"applicable_stages": []}, "script")


def test_validate_applicable_stages():
    assert validate_applicable_stages(["character", "invalid", "script"]) == ["character", "script"]


def test_embed_text_cosine_self():
    v = embed_text("动画短片叙事")
    assert len(v) == 384
    assert cosine_similarity(v, v) > 0.99


def test_search_knowledge_hits_with_stage():
    sample = [{"entry_id": "kb.anim1", "title": "动画短片", "summary": "参考", "match_keywords": ["动画"]}]

    with patch("app.services.drama_knowledge_service.get_drama_knowledge_service") as mock_get:
        svc = AsyncMock()
        svc.search = AsyncMock(return_value=sample)
        mock_get.return_value = svc

        hits = asyncio.run(
            search_knowledge_hits("动画短片参考", stage="character", top_k=5)
        )
        assert len(hits) == 1
        svc.search.assert_awaited_once()
        call_kw = svc.search.await_args.kwargs
        assert call_kw.get("stage") == "character"


def test_list_category_codes_for_stage_mock():
    svc = DramaKnowledgeService()

    class FakeCursor:
        def __init__(self, items):
            self._items = items

        def sort(self, *_):
            return self

        def __aiter__(self):
            async def gen():
                for item in self._items:
                    yield item

            return gen()

    svc._cat_collection = AsyncMock()
    svc.cat_collection.find = lambda *_: FakeCursor(
        [
            {"code": "anime", "applicable_stages": ["character", "production"]},
            {"code": "script_only", "applicable_stages": ["script"]},
        ]
    )
    svc.ensure_categories_seeded = AsyncMock()

    codes = asyncio.run(svc.list_category_codes_for_stage("character"))
    assert "anime" in codes
    assert "script_only" not in codes
