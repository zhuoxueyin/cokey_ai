"""协议画像 CRUD + 内置种子合并加载。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from bson import ObjectId

from app.core.builtin_protocol_profiles import BUILTIN_PROFILE_BY_ID, BUILTIN_PROTOCOL_PROFILES
from app.core.logging_config import get_logger

logger = get_logger()


class ProtocolProfileService:
    def __init__(self):
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            try:
                from app.core.database import get_db
                db = get_db()
                if db is not None:
                    self._collection = db["protocol_profiles"]
            except Exception:
                self._collection = None
        return self._collection

    async def ensure_builtin_seeded(self) -> int:
        """启动时将内置画像 upsert 到 DB（仅插入缺失项，不覆盖运维修改）。"""
        if self.collection is None:
            return 0
        inserted = 0
        now = datetime.utcnow()
        for profile in BUILTIN_PROTOCOL_PROFILES:
            existing = await self.collection.find_one({"profile_id": profile["profile_id"]})
            if existing:
                continue
            doc = {**profile, "created_at": now, "updated_at": now}
            await self.collection.insert_one(doc)
            inserted += 1
        if inserted:
            logger.info(f"协议画像种子写入 {inserted} 条")
        await self._migrate_volcengine_multimodal_slot()
        await self._migrate_chat_image_protocol_slots()
        return inserted

    async def _migrate_chat_image_protocol_slots(self) -> None:
        """对话式生图槽位拆分为 text_to_image / image_to_image（幂等）。"""
        if self.collection is None:
            return
        now = datetime.utcnow()
        for pid, src in BUILTIN_PROFILE_BY_ID.items():
            slot = src.get("protocol_slot", "")
            if slot not in (
                "openai.chat.image.text_to_image",
                "openai.chat.image.image_to_image",
            ):
                continue
            await self.collection.update_one(
                {"profile_id": pid},
                {
                    "$set": {
                        "protocol_slot": slot,
                        "name": src.get("name"),
                        "description": src.get("description"),
                        "updated_at": now,
                    }
                },
            )

    async def _migrate_volcengine_multimodal_slot(self) -> None:
        """将火山视频画像升级为多模态统一槽位（幂等）。"""
        if self.collection is None:
            return
        now = datetime.utcnow()
        for pid in ("volcengine.video.text_to_video", "volcengine.video.image_to_video"):
            src = BUILTIN_PROFILE_BY_ID.get(pid)
            if not src:
                continue
            await self.collection.update_one(
                {"profile_id": pid},
                {
                    "$set": {
                        "protocol_slot": src["protocol_slot"],
                        "endpoint_type": src["endpoint_type"],
                        "name": src["name"],
                        "description": src.get("description"),
                        "request": src.get("request"),
                        "http": src.get("http"),
                        "updated_at": now,
                    }
                },
            )

    async def get_by_profile_id(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """DB 优先，其次内置。"""
        builtin = BUILTIN_PROFILE_BY_ID.get(profile_id)
        doc = None
        try:
            if self.collection is not None:
                doc = await self.collection.find_one(
                    {"profile_id": profile_id, "status": {"$ne": "deleted"}}
                )
        except Exception:
            doc = None
        if doc:
            return self._to_response(doc)
        if builtin and builtin.get("status", "active") == "active":
            return {**builtin, "id": f"builtin:{profile_id}"}
        return None

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        existing = await self.collection.find_one({"profile_id": data["profile_id"]})
        if existing:
            raise ValueError(f"协议画像已存在: {data['profile_id']}")
        now = datetime.utcnow()
        doc = {
            **data,
            "is_builtin": data.get("is_builtin", False),
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return self._to_response(doc)

    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        if doc_id.startswith("builtin:"):
            return await self.get_by_profile_id(doc_id.removeprefix("builtin:"))
        if not ObjectId.is_valid(doc_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(doc_id)})
        return self._to_response(doc) if doc else None

    async def list(
        self,
        page: int = 1,
        page_size: int = 50,
        provider: Optional[str] = None,
        invocation_mode: Optional[str] = None,
        status: Optional[str] = None,
        include_builtin: bool = True,
    ) -> Tuple[List[Dict[str, Any]], int]:
        query: Dict[str, Any] = {}
        if provider:
            query["provider"] = provider
        if invocation_mode:
            query["invocation_mode"] = invocation_mode
        if status:
            query["status"] = status
        else:
            query["status"] = {"$ne": "deleted"}

        cursor = (
            self.collection.find(query)
            .sort("profile_id", 1)
            .skip((page - 1) * page_size)
            .limit(page_size)
        )
        db_docs = [self._to_response(doc) async for doc in cursor]
        db_total = await self.collection.count_documents(query)

        if not include_builtin:
            return db_docs, db_total

        # 合并内置（DB 同 profile_id 已覆盖）
        db_ids = {d["profile_id"] for d in db_docs}
        merged = list(db_docs)
        for pid, builtin in BUILTIN_PROFILE_BY_ID.items():
            if pid in db_ids:
                continue
            if provider and builtin.get("provider") not in (provider, "*"):
                continue
            if invocation_mode and builtin.get("invocation_mode") != invocation_mode:
                continue
            if status and builtin.get("status") != status:
                continue
            merged.append({**builtin, "id": f"builtin:{pid}"})

        merged.sort(key=lambda x: x.get("profile_id", ""))
        total = db_total + len(merged) - len(db_docs)
        start = (page - 1) * page_size
        return merged[start : start + page_size], total

    async def update(self, doc_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if doc_id.startswith("builtin:"):
            profile_id = doc_id.removeprefix("builtin:")
            existing = await self.collection.find_one({"profile_id": profile_id})
            if not existing:
                base = BUILTIN_PROFILE_BY_ID.get(profile_id)
                if not base:
                    return None
                now = datetime.utcnow()
                doc = {**base, **data, "profile_id": profile_id, "created_at": now, "updated_at": now}
                result = await self.collection.insert_one(doc)
                doc["_id"] = result.inserted_id
                return self._to_response(doc)
            doc_id = str(existing["_id"])

        if not ObjectId.is_valid(doc_id):
            return None
        data = {k: v for k, v in data.items() if v is not None}
        data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": data},
        )
        if result.matched_count == 0:
            return None
        doc = await self.collection.find_one({"_id": ObjectId(doc_id)})
        return self._to_response(doc) if doc else None

    async def delete(self, doc_id: str) -> bool:
        if doc_id.startswith("builtin:"):
            profile_id = doc_id.removeprefix("builtin:")
            builtin = BUILTIN_PROFILE_BY_ID.get(profile_id)
            if not builtin:
                return False
            existing = await self.collection.find_one({"profile_id": profile_id})
            if existing:
                doc_id = str(existing["_id"])
            else:
                now = datetime.utcnow()
                await self.collection.insert_one({
                    **builtin,
                    "status": "deleted",
                    "created_at": now,
                    "updated_at": now,
                })
                return True
        if not ObjectId.is_valid(doc_id):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"status": "deleted", "updated_at": datetime.utcnow()}},
        )
        return result.matched_count > 0

    def _to_response(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(doc["_id"]),
            "profile_id": doc["profile_id"],
            "name": doc.get("name", ""),
            "provider": doc.get("provider"),
            "protocol_slot": doc.get("protocol_slot", ""),
            "invocation_mode": doc.get("invocation_mode", ""),
            "endpoint_type": doc.get("endpoint_type", ""),
            "http": doc.get("http", {}),
            "request": doc.get("request", {}),
            "response": doc.get("response", {}),
            "description": doc.get("description"),
            "status": doc.get("status", "active"),
            "is_builtin": doc.get("is_builtin", False),
            "created_at": doc.get("created_at"),
            "updated_at": doc.get("updated_at"),
        }


_service: Optional[ProtocolProfileService] = None


def get_protocol_profile_service() -> ProtocolProfileService:
    global _service
    if _service is None:
        _service = ProtocolProfileService()
    return _service
