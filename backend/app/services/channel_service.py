from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from app.core.database import get_collection
from app.core.config import settings
from app.core.security import encrypt_string, decrypt_string, mask_string
from app.core.logging_config import get_logger
from bson import ObjectId

logger = get_logger()


class ChannelService:
    def __init__(self):
        self.collection = get_collection("channels")

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow()
        doc = {
            "channel_code": data["channel_code"],
            "channel_name": data["channel_name"],
            "channel_type": data["channel_type"],
            "base_url": data["base_url"],
            "auth_config": self._encrypt_auth(data.get("auth_config", {})),
            "retry_config": data.get("retry_config", {"timeout": 30, "max_retries": 3, "retry_delay": 2}),
            "rate_limit_config": data.get("rate_limit_config", {"requests_per_minute": 60}),
            "status": data.get("status", "active"),
            "description": data.get("description", ""),
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return self._to_response(doc)

    async def get_by_id(self, channel_id: str) -> Optional[Dict[str, Any]]:
        if not ObjectId.is_valid(channel_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(channel_id)})
        return self._to_response(doc) if doc else None

    async def get_by_code(self, channel_code: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"channel_code": channel_code})
        return self._to_response_with_plain(doc) if doc else None

    async def list(self, page: int = 1, page_size: int = 20, status: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
        query = {}
        if status:
            query["status"] = status
        cursor = self.collection.find(query).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
        total = await self.collection.count_documents(query)
        docs = []
        async for doc in cursor:
            docs.append(self._to_response(doc))
        return docs, total

    async def update(self, channel_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not ObjectId.is_valid(channel_id):
            return None
        update_data = {}
        if "channel_name" in data:
            update_data["channel_name"] = data["channel_name"]
        if "channel_type" in data:
            update_data["channel_type"] = data["channel_type"]
        if "base_url" in data:
            update_data["base_url"] = data["base_url"]
        if "auth_config" in data:
            update_data["auth_config"] = self._encrypt_auth(data["auth_config"])
        if "retry_config" in data:
            update_data["retry_config"] = data["retry_config"]
        if "rate_limit_config" in data:
            update_data["rate_limit_config"] = data["rate_limit_config"]
        if "status" in data:
            update_data["status"] = data["status"]
        if "description" in data:
            update_data["description"] = data["description"]
        update_data["updated_at"] = datetime.utcnow()

        result = await self.collection.update_one({"_id": ObjectId(channel_id)}, {"$set": update_data})
        if result.modified_count > 0:
            return await self.get_by_id(channel_id)
        return None

    async def delete(self, channel_id: str) -> bool:
        if not ObjectId.is_valid(channel_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(channel_id)})
        return result.deleted_count > 0

    async def set_status(self, channel_id: str, status: str) -> bool:
        if not ObjectId.is_valid(channel_id):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(channel_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def _encrypt_auth(self, auth_config: Dict[str, Any]) -> Dict[str, Any]:
        encrypted = {}
        for key, value in auth_config.items():
            if value and isinstance(value, str):
                encrypted[key] = encrypt_string(value, settings.encryption_key)
            else:
                encrypted[key] = value
        return encrypted

    def _decrypt_auth(self, auth_config: Dict[str, Any]) -> Dict[str, Any]:
        decrypted = {}
        for key, value in auth_config.items():
            if value and isinstance(value, str):
                decrypted[key] = decrypt_string(value, settings.encryption_key)
            else:
                decrypted[key] = value
        return decrypted

    def _to_response(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(doc["_id"]),
            "channel_code": doc["channel_code"],
            "channel_name": doc["channel_name"],
            "channel_type": doc["channel_type"],
            "base_url": doc["base_url"],
            "auth_config": self._mask_auth(doc.get("auth_config", {})),
            "retry_config": doc.get("retry_config", {}),
            "rate_limit_config": doc.get("rate_limit_config", {}),
            "status": doc["status"],
            "description": doc.get("description", ""),
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }

    def _to_response_with_plain(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(doc["_id"]),
            "channel_code": doc["channel_code"],
            "channel_name": doc["channel_name"],
            "channel_type": doc["channel_type"],
            "base_url": doc["base_url"],
            "auth_config": self._decrypt_auth(doc.get("auth_config", {})),
            "retry_config": doc.get("retry_config", {}),
            "rate_limit_config": doc.get("rate_limit_config", {}),
            "status": doc["status"],
            "description": doc.get("description", ""),
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }

    def _mask_auth(self, auth_config: Dict[str, Any]) -> Dict[str, Any]:
        return {k: mask_string(decrypt_string(str(v), settings.encryption_key)) if v else "" for k, v in auth_config.items()}


_channel_service = None


def get_channel_service() -> ChannelService:
    global _channel_service
    if _channel_service is None:
        _channel_service = ChannelService()
    return _channel_service
