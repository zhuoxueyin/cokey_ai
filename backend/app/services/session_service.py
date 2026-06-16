from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from app.core.database import get_collection
from app.core.logging_config import get_logger
from app.core.utils import generate_task_id, generate_session_id
from bson import ObjectId

logger = get_logger()


class SessionService:
    def __init__(self):
        self.collection = get_collection("sessions")

    async def create(self, category: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.utcnow()
        session_id = generate_session_id()
        doc = {
            "session_id": session_id,
            "user_id": user_id,           # 新增：用户ID，用于多用户隔离
            "category": category,
            "task_ids": [],
            "context": {},                # 新增：会话上下文，用于对话历史共享
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return self._to_response(doc)

    async def get_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"session_id": session_id})
        return self._to_response(doc) if doc else None

    async def add_task(self, session_id: str, task_id: str) -> bool:
        result = await self.collection.update_one(
            {"session_id": session_id},
            {"$addToSet": {"task_ids": task_id}, "$set": {"updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def update_context(self, session_id: str, context: Dict[str, Any]) -> bool:
        """更新会话上下文（用于对话历史共享）"""
        result = await self.collection.update_one(
            {"session_id": session_id},
            {"$set": {"context": context, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def append_context(self, session_id: str, key: str, value: Any) -> bool:
        """向会话上下文中追加数据"""
        result = await self.collection.update_one(
            {"session_id": session_id},
            {"$set": {f"context.{key}": value, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def list_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """按用户ID查询会话列表"""
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1)
        docs = []
        async for doc in cursor:
            docs.append(self._to_response(doc))
        return docs

    def _to_response(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(doc["_id"]),
            "session_id": doc["session_id"],
            "user_id": doc.get("user_id"),
            "category": doc["category"],
            "task_ids": doc.get("task_ids", []),
            "context": doc.get("context", {}),
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }


_session_service = None


def get_session_service() -> SessionService:
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
