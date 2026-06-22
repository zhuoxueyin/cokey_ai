"""短剧项目 CRUD + 阶段状态。"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.logging_config import get_logger

logger = get_logger()

STAGES = [
    "init",
    "concept",
    "outline",
    "script",
    "character",
    "scene",
    "storyboard",
    "prompt_pack",
    "production",
]


class DramaProjectService:
    COLLECTION = "drama_projects"

    def __init__(self):
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            from app.core.database import get_collection
            self._collection = get_collection(self.COLLECTION)
        return self._collection

    async def ensure_indexes(self) -> None:
        await self.collection.create_index("project_id", unique=True, name="uniq_project_id")
        await self.collection.create_index("user_id", name="idx_user_id")
        await self.collection.create_index("stage", name="idx_stage")

    def _serialize(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        out = {k: v for k, v in doc.items() if k != "_id"}
        out["id"] = str(doc["_id"])
        for field in ("created_at", "updated_at"):
            if doc.get(field):
                out[field] = doc[field].isoformat() + "Z"
        return out

    async def get_by_project_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"project_id": project_id, "deleted_at": None})
        return self._serialize(doc) if doc else None

    async def list(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        query: Dict[str, Any] = {"deleted_at": None}
        if user_id:
            query["user_id"] = user_id
        total = await self.collection.count_documents(query)
        skip = (page - 1) * page_size
        cursor = self.collection.find(query).sort("updated_at", -1).skip(skip).limit(page_size)
        return [self._serialize(d) async for d in cursor], total

    async def create(self, data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.utcnow()
        project_id = f"drp_{uuid.uuid4().hex[:16]}"
        doc = {
            "project_id": project_id,
            "title": data["title"],
            "stage": "init",
            "genre": data.get("genre", ""),
            "target_platform": data.get("target_platform", "竖屏短剧"),
            "episode_count": data.get("episode_count", 20),
            "episode_duration_sec": data.get("episode_duration_sec", 90),
            "style_preset_id": data.get("style_preset_id"),
            "style_modifiers": data.get("style_modifiers", []),
            "canvas_project_id": None,
            "session_id": None,
            "user_id": user_id,
            "confirmed_settings": [],
            "forbidden_settings": [],
            "brief": {},
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        logger.info(f"创建短剧项目: {project_id}")
        return self._serialize(doc)

    async def update(self, project_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"project_id": project_id, "deleted_at": None})
        if not doc:
            return None
        if "stage" in data and data["stage"] not in STAGES:
            raise ValueError(f"无效 stage: {data['stage']}")
        update_data = {**data, "updated_at": datetime.utcnow()}
        await self.collection.update_one({"_id": doc["_id"]}, {"$set": update_data})
        return await self.get_by_project_id(project_id)

    async def soft_delete(self, project_id: str) -> bool:
        result = await self.collection.update_one(
            {"project_id": project_id},
            {"$set": {"deleted_at": datetime.utcnow()}},
        )
        return result.modified_count > 0

    async def get_memory_snapshot(self, project_id: str) -> Dict[str, Any]:
        project = await self.get_by_project_id(project_id)
        if not project:
            return {}
        return {
            "project": project,
            "characters": [],
            "scenes": [],
            "episodes": [],
            "shots": [],
            "confirmed_settings": project.get("confirmed_settings", []),
            "forbidden_settings": project.get("forbidden_settings", []),
        }


_drama_project_service: Optional[DramaProjectService] = None


def get_drama_project_service() -> DramaProjectService:
    global _drama_project_service
    if _drama_project_service is None:
        _drama_project_service = DramaProjectService()
    return _drama_project_service
