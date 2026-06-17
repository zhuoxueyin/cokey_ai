from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from app.core.database import get_collection
from app.core.config import settings
from app.core.logging_config import get_logger
from bson import ObjectId

logger = get_logger()


def _mask_string(value: str, keep_start: int = 4, keep_end: int = 4) -> str:
    """对敏感字符串做脱敏处理：保留前后字符，中间用 * 代替"""
    if not value or not isinstance(value, str):
        return value or ""
    if len(value) <= keep_start + keep_end:
        return "*" * len(value)
    return value[:keep_start] + "*" * (len(value) - keep_start - keep_end) + value[-keep_end:]


class ChannelService:
    def __init__(self):
        self.collection = get_collection("channels")

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow()
        doc = {
            "channel_code": data["channel_code"],
            "channel_name": data["channel_name"],
            "channel_type": data["channel_type"],
            "channel_provider": data.get("channel_provider"),
            "base_url": data["base_url"],
            "auth_config": data.get("auth_config", {}),
            "api_config": data.get("api_config", {
                "text_path": "/chat/completions",
                "image_path": "/images/generations",
                "video_path": "/videos/generations",
                "text_stream": True,
            }),
            "endpoints": data.get("endpoints", []),
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
        """给内部网关调用：返回完整的明文 auth_config"""
        doc = await self.collection.find_one({"channel_code": channel_code})
        if not doc:
            return None
        return self._to_internal_response(doc)

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
        for key in ["channel_name", "channel_type", "channel_provider", "base_url", "description"]:
            if key in data:
                update_data[key] = data[key]
        if "auth_config" in data:
            update_data["auth_config"] = data["auth_config"]
        if "api_config" in data:
            update_data["api_config"] = data["api_config"]
        if "endpoints" in data:
            update_data["endpoints"] = data["endpoints"]
        if "retry_config" in data:
            update_data["retry_config"] = data["retry_config"]
        if "rate_limit_config" in data:
            update_data["rate_limit_config"] = data["rate_limit_config"]
        if "status" in data:
            update_data["status"] = data["status"]
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

    def _mask_auth(self, auth_config: Dict[str, Any]) -> Dict[str, Any]:
        """给管理后台返回：直接返回明文（不脱敏）"""
        return auth_config or {}

    def _to_response(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """对外返回（管理后台列表/详情）：auth_config 做脱敏"""
        return {
            "id": str(doc["_id"]),
            "channel_code": doc["channel_code"],
            "channel_name": doc["channel_name"],
            "channel_type": doc["channel_type"],
            "channel_provider": doc.get("channel_provider"),
            "base_url": doc["base_url"],
            "auth_config": self._mask_auth(doc.get("auth_config", {})),
            "api_config": doc.get("api_config", {
                "text_path": "/chat/completions",
                "image_path": "/images/generations",
                "video_path": "/videos/generations",
                "text_stream": True,
            }),
            "endpoints": doc.get("endpoints", []),
            "retry_config": doc.get("retry_config", {}),
            "rate_limit_config": doc.get("rate_limit_config", {}),
            "status": doc["status"],
            "description": doc.get("description", ""),
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }

    def _to_internal_response(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """给内部网关调用：auth_config 保持明文"""
        return {
            "id": str(doc["_id"]),
            "channel_code": doc["channel_code"],
            "channel_name": doc["channel_name"],
            "channel_type": doc["channel_type"],
            "channel_provider": doc.get("channel_provider"),
            "base_url": doc["base_url"],
            "auth_config": doc.get("auth_config", {}),
            "api_config": doc.get("api_config", {
                "text_path": "/chat/completions",
                "image_path": "/images/generations",
                "video_path": "/videos/generations",
                "text_stream": True,
            }),
            "endpoints": doc.get("endpoints", []),
            "retry_config": doc.get("retry_config", {}),
            "rate_limit_config": doc.get("rate_limit_config", {}),
            "status": doc["status"],
            "description": doc.get("description", ""),
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }


_channel_service = None


def get_channel_service() -> ChannelService:
    global _channel_service
    if _channel_service is None:
        _channel_service = ChannelService()
    return _channel_service
