"""知识库分类删除（含内置分类）。"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.drama_knowledge_service import DramaKnowledgeService


def test_delete_builtin_category_suppresses_reseed():
    async def _run():
        svc = DramaKnowledgeService()
        cat_col = AsyncMock()
        cat_col.find_one = AsyncMock(
            return_value={"code": "aigc", "name": "AIGC", "builtin": True}
        )
        cat_col.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
        entry_col = AsyncMock()
        entry_col.count_documents = AsyncMock(return_value=0)
        svc._cat_collection = cat_col
        svc._collection = entry_col

        suppress = AsyncMock()
        with patch.object(svc, "_suppress_builtin_category", suppress):
            with patch.object(svc, "_is_builtin_category_code", return_value=True):
                ok = await svc.delete_category("aigc")

        assert ok is True
        suppress.assert_awaited_once_with("aigc")
        cat_col.delete_one.assert_awaited_once_with({"code": "aigc"})

    asyncio.run(_run())


def test_delete_category_with_entries_raises():
    async def _run():
        svc = DramaKnowledgeService()
        cat_col = AsyncMock()
        cat_col.find_one = AsyncMock(return_value={"code": "film", "name": "电影"})
        entry_col = AsyncMock()
        entry_col.count_documents = AsyncMock(return_value=2)
        svc._cat_collection = cat_col
        svc._collection = entry_col

        with pytest.raises(ValueError, match="仍有 2 条知识"):
            await svc.delete_category("film")

    asyncio.run(_run())
