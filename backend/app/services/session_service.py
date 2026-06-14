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

    async def create(self, category: str) -> Dict[str, Any]:
        now = datetime.utcnow()
        session_id = generate_session_id()
        doc = {
            "session_id": session_id,
            "category": category,
            "task_ids": [],
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

    def _to_response(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(doc["_id"]),
            "session_id": doc["session_id"],
            "category": doc["category"],
            "task_ids": doc.get("task_ids", []),
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }


_session_service = None


def get_session_service() -> SessionService:
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
