"""短剧风格库 CRUD — 数据以风格广场（MongoDB drama_style_presets）为唯一来源。"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.drama.style_model_protocol import build_model_protocol, merge_protocol_into_doc
from app.core.drama.style_spec_defaults import build_style_spec_document
from app.core.logging_config import get_logger

logger = get_logger()


class DramaStyleService:
    COLLECTION = "drama_style_presets"

    def __init__(self):
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            from app.core.database import get_collection
            self._collection = get_collection(self.COLLECTION)
        return self._collection

    async def ensure_indexes(self) -> None:
        await self.collection.create_index("style_id", unique=True, name="uniq_style_id")
        await self.collection.create_index("render_class", name="idx_render_class")
        await self.collection.create_index("status", name="idx_status")
        await self.collection.create_index([("name", "text"), ("genre_tags", "text")], name="text_search")

    def _serialize(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        out = {k: v for k, v in doc.items() if k != "_id"}
        out["id"] = str(doc["_id"])
        if doc.get("created_at"):
            out["created_at"] = doc["created_at"].isoformat() + "Z"
        if doc.get("updated_at"):
            out["updated_at"] = doc["updated_at"].isoformat() + "Z"
        if doc.get("published_at"):
            out["published_at"] = doc["published_at"].isoformat() + "Z"
        if not out.get("model_protocol"):
            out["model_protocol"] = build_model_protocol(out)
        return out

    async def get_by_style_id(self, style_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"style_id": style_id, "deleted_at": None})
        return self._serialize(doc) if doc else None

    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        try:
            doc = await self.collection.find_one({"_id": ObjectId(doc_id), "deleted_at": None})
        except Exception:
            return None
        return self._serialize(doc) if doc else None

    async def list(
        self,
        page: int = 1,
        page_size: int = 50,
        render_class: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        query: Dict[str, Any] = {"deleted_at": None}
        if render_class:
            query["render_class"] = render_class
        if status:
            query["status"] = status

        if keyword:
            query["$or"] = [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"style_id": {"$regex": keyword, "$options": "i"}},
                {"genre_tags": {"$regex": keyword, "$options": "i"}},
            ]

        total = await self.collection.count_documents(query)
        skip = (page - 1) * page_size
        cursor = (
            self.collection.find(query)
            .sort([("updated_at", -1), ("name", 1)])
            .skip(skip)
            .limit(page_size)
        )
        items = [self._serialize(d) async for d in cursor]
        return items, total

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        from app.core.drama.style_description import enrich_style_payload

        data = enrich_style_payload(dict(data))
        now = datetime.utcnow()
        style_id = data.get("style_id") or f"style_{uuid.uuid4().hex[:12]}"
        existing = await self.collection.find_one({"style_id": style_id})
        if existing:
            raise ValueError(f"style_id 已存在: {style_id}")

        publish = bool(data.pop("publish", False))
        doc = {
            **build_style_spec_document(
                {
                    "style_id": style_id,
                    "name": data["name"],
                    "render_class": data.get("render_class", "live_action"),
                    "genre_tags": data.get("genre_tags", []),
                    "origin": data.get("origin", "manual"),
                    "cover_url": data.get("cover_url"),
                }
            ),
            **{k: v for k, v in data.items() if k not in ("style_id", "name")},
            "style_id": style_id,
            "origin": data.get("origin", "manual"),
            "cover_asset_id": data.get("cover_asset_id"),
            "status": "published" if publish else data.get("status", "draft"),
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }
        if publish:
            doc["published_at"] = now
        if data.get("model_prompts"):
            doc["model_prompts"] = {**(doc.get("model_prompts") or {}), **data["model_prompts"]}
        if data.get("visual"):
            doc["visual"] = {**(doc.get("visual") or {}), **data["visual"]}
        if data.get("reference_images"):
            doc["reference_images"] = data["reference_images"]
        doc = merge_protocol_into_doc(doc)
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        logger.info(f"创建风格 preset: {style_id}")
        return self._serialize(doc)

    async def update(self, style_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"style_id": style_id, "deleted_at": None})
        if not doc:
            return None
        update_data = {**data, "updated_at": datetime.utcnow()}
        from app.core.drama.style_description import enrich_style_payload

        update_data = enrich_style_payload(update_data)
        if any(
            k in update_data
            for k in (
                "model_prompts",
                "visual",
                "genre_tags",
                "render_class",
                "reference_images",
                "cover_asset_id",
                "style_description_md",
            )
        ):
            merged = {**doc, **update_data}
            update_data["model_protocol"] = build_model_protocol(merged)
        await self.collection.update_one({"_id": doc["_id"]}, {"$set": update_data})
        return await self.get_by_style_id(style_id)

    async def publish(self, style_id: str) -> Optional[Dict[str, Any]]:
        doc = (await self.get_by_style_id(style_id)) or {}
        from app.core.drama.style_description import validate_for_publish

        validate_for_publish(doc)
        now = datetime.utcnow()
        await self.collection.update_one(
            {"style_id": style_id},
            {"$set": {"status": "published", "published_at": now, "updated_at": now}},
        )
        return await self.get_by_style_id(style_id)

    async def soft_delete(self, style_id: str, *, allow_seed: bool = False) -> bool:
        doc = await self.collection.find_one({"style_id": style_id, "deleted_at": None})
        if not doc:
            return False
        if doc.get("immutable") and not allow_seed:
            raise ValueError("该风格已锁定，不可删除")
        result = await self.collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"deleted_at": datetime.utcnow(), "status": "archived"}},
        )
        return result.modified_count > 0

    async def ensure_model_protocol_complete(self) -> int:
        """为缺失或过期的 model_protocol 批量补全。"""
        updated = 0
        query = {
            "deleted_at": None,
            "$or": [
                {"model_protocol": {"$exists": False}},
                {"model_protocol.version": {"$ne": "1.0"}},
            ],
        }
        cursor = self.collection.find(query)
        async for doc in cursor:
            proto = build_model_protocol(doc)
            await self.collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"model_protocol": proto, "updated_at": datetime.utcnow()}},
            )
            updated += 1
        if updated:
            logger.info(f"补全 model_protocol: {updated} 条")
        return updated


_drama_style_service: Optional[DramaStyleService] = None


def get_drama_style_service() -> DramaStyleService:
    global _drama_style_service
    if _drama_style_service is None:
        _drama_style_service = DramaStyleService()
    return _drama_style_service
