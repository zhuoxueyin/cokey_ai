"""风格软删单元测试。"""
import asyncio

import pytest

from app.services.drama_style_service import DramaStyleService


def test_soft_delete_blocks_immutable():
    svc = DramaStyleService()

    class FakeCollection:
        async def find_one(self, query):
            return {"_id": "x", "style_id": "locked_style", "immutable": True, "deleted_at": None}

    svc._collection = FakeCollection()

    with pytest.raises(ValueError, match="已锁定"):
        asyncio.run(svc.soft_delete("locked_style"))


def test_soft_delete_allows_seed_origin():
    svc = DramaStyleService()
    updated = {}

    class FakeCollection:
        async def find_one(self, query):
            return {"_id": "x", "style_id": "seed_style", "origin": "seed", "deleted_at": None}

        async def update_one(self, filt, upd):
            updated["called"] = True
            return type("R", (), {"modified_count": 1})()

    svc._collection = FakeCollection()
    ok = asyncio.run(svc.soft_delete("seed_style"))
    assert ok is True
    assert updated.get("called")


def test_soft_delete_allow_immutable_with_flag():
    svc = DramaStyleService()
    updated = {}

    class FakeCollection:
        async def find_one(self, query):
            return {"_id": "x", "style_id": "locked_style", "immutable": True, "deleted_at": None}

        async def update_one(self, filt, upd):
            updated["called"] = True
            return type("R", (), {"modified_count": 1})()

    svc._collection = FakeCollection()
    ok = asyncio.run(svc.soft_delete("locked_style", allow_seed=True))
    assert ok is True
    assert updated.get("called")
