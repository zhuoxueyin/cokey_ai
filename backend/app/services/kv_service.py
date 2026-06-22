"""MongoDB KV 封装（短剧 Agent 等模块使用）。"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.database import get_collection
from app.core.logging_config import get_logger

logger = get_logger()

COLLECTION = "kv_store"


class KVService:
    def __init__(self):
        self.collection = get_collection(COLLECTION)

    @staticmethod
    def _key_doc(namespace: str, key: str) -> Dict[str, str]:
        return {"namespace": namespace, "key": key}

    async def ensure_indexes(self) -> None:
        await self.collection.create_index(
            [("namespace", 1), ("key", 1)],
            unique=True,
            name="uniq_namespace_key",
        )
        await self.collection.create_index(
            [("expires_at", 1)],
            expireAfterSeconds=0,
            name="ttl_expires_at",
        )

    async def get(self, namespace: str, key: str, default: Any = None) -> Any:
        doc = await self.collection.find_one(self._key_doc(namespace, key))
        if not doc:
            return default
        if doc.get("expires_at") and doc["expires_at"] < datetime.utcnow():
            await self.delete(namespace, key)
            return default
        return doc.get("value", default)

    async def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        now = datetime.utcnow()
        doc: Dict[str, Any] = {
            "namespace": namespace,
            "key": key,
            "value": value,
            "updated_at": now,
        }
        if ttl_seconds is not None and ttl_seconds > 0:
            doc["expires_at"] = now + timedelta(seconds=ttl_seconds)
        else:
            doc["expires_at"] = None

        existing = await self.collection.find_one(self._key_doc(namespace, key))
        if existing:
            doc["created_at"] = existing.get("created_at", now)
            await self.collection.update_one({"_id": existing["_id"]}, {"$set": doc})
        else:
            doc["created_at"] = now
            await self.collection.insert_one(doc)

        return {"namespace": namespace, "key": key, "ttl_seconds": ttl_seconds}

    async def delete(self, namespace: str, key: str) -> bool:
        result = await self.collection.delete_one(self._key_doc(namespace, key))
        return result.deleted_count > 0

    async def mget(self, namespace: str, keys: List[str]) -> Dict[str, Any]:
        if not keys:
            return {}
        cursor = self.collection.find({"namespace": namespace, "key": {"$in": keys}})
        out: Dict[str, Any] = {}
        now = datetime.utcnow()
        async for doc in cursor:
            if doc.get("expires_at") and doc["expires_at"] < now:
                continue
            out[doc["key"]] = doc.get("value")
        return out

    async def list_keys(self, namespace: str, prefix: str = "") -> List[str]:
        query: Dict[str, Any] = {"namespace": namespace}
        if prefix:
            query["key"] = {"$regex": f"^{prefix}"}
        cursor = self.collection.find(query, {"key": 1})
        return [d["key"] async for d in cursor]

    async def get_json(self, namespace: str, key: str, default: Any = None) -> Any:
        val = await self.get(namespace, key, default=None)
        if val is None:
            return default
        if isinstance(val, str):
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return val
        return val

    async def set_json(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        return await self.set(namespace, key, value, ttl_seconds=ttl_seconds)


_kv_service: Optional[KVService] = None


def get_kv_service() -> KVService:
    global _kv_service
    if _kv_service is None:
        _kv_service = KVService()
    return _kv_service
