from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from app.core.database import get_collection
from app.core.logging_config import get_logger
from bson import ObjectId

logger = get_logger()


class ModelService:
    def __init__(self):
        self.collection = get_collection("models")

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow()
        if data.get("is_default", False):
            await self.collection.update_many({"category": data["category"]}, {"$set": {"is_default": False}})

        doc = {
            "model_code": data["model_code"],
            "model_name": data["model_name"],
            "category": data["category"],
            "cover": data.get("cover", ""),
            "description": data.get("description", ""),
            "tags": data.get("tags", []),
            "channel_bindings": data.get("channel_bindings", []),
            "param_schema": data.get("param_schema", {"fields": []}),
            "supported_inputs": data.get("supported_inputs", {}),
            "status": data.get("status", "online"),
            "sort_order": data.get("sort_order", 0),
            "is_default": data.get("is_default", False),
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return self._to_response(doc)

    async def get_by_id(self, model_id: str) -> Optional[Dict[str, Any]]:
        if not ObjectId.is_valid(model_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(model_id)})
        return self._to_response(doc) if doc else None

    async def get_by_code(self, model_code: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"model_code": model_code})
        return self._to_response(doc) if doc else None

    async def get_default(self, category: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"category": category, "is_default": True, "status": "online"})
        if doc:
            return self._to_response(doc)
        doc = await self.collection.find_one({"category": category, "status": "online"})
        return self._to_response(doc) if doc else None

    async def list(self, page: int = 1, page_size: int = 20, category: Optional[str] = None,
                   status: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
        query = {}
        if category:
            query["category"] = category
        if status:
            query["status"] = status
        cursor = self.collection.find(query).sort([("sort_order", -1), ("created_at", -1)]).skip((page - 1) * page_size).limit(page_size)
        total = await self.collection.count_documents(query)
        docs = []
        async for doc in cursor:
            docs.append(self._to_response(doc))
        return docs, total

    async def list_public(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {"status": "online"}
        if category:
            query["category"] = category
        cursor = self.collection.find(query).sort([("is_default", -1), ("sort_order", -1), ("created_at", -1)])
        docs = []
        async for doc in cursor:
            docs.append(self._to_public_item(doc))
        return docs

    async def update(self, model_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not ObjectId.is_valid(model_id):
            return None
        update_data = {}
        for key in ["model_name", "category", "cover", "description", "tags",
                    "param_schema", "supported_inputs", "status", "sort_order", "is_default"]:
            if key in data:
                update_data[key] = data[key]
        if "channel_bindings" in data and data["channel_bindings"] is not None:
            update_data["channel_bindings"] = data["channel_bindings"]

        if data.get("is_default") and update_data.get("is_default"):
            existing = await self.get_by_id(model_id)
            cat = existing.get("category") if existing else update_data.get("category")
            if cat:
                await self.collection.update_many({"category": cat, "_id": {"$ne": ObjectId(model_id)}}, {"$set": {"is_default": False}})

        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one({"_id": ObjectId(model_id)}, {"$set": update_data})
        if result.modified_count > 0:
            return await self.get_by_id(model_id)
        return None

    async def delete(self, model_id: str) -> bool:
        if not ObjectId.is_valid(model_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(model_id)})
        return result.deleted_count > 0

    async def set_status(self, model_id: str, status: str) -> bool:
        if not ObjectId.is_valid(model_id):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(model_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def batch_import(self, channel_code: str, models_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        channel = None
        from app.services.channel_service import get_channel_service
        channel_svc = get_channel_service()
        channel = await channel_svc.get_by_code(channel_code)
        if not channel:
            return {"total": 0, "imported": 0, "skipped": 0, "failed": len(models_data),
                    "messages": [f"渠道不存在: {channel_code}"]}

        imported = 0
        skipped = 0
        failed = 0
        messages = []

        for item in models_data:
            try:
                model_code = item.get("model_code", item.get("id", ""))
                if not model_code:
                    failed += 1
                    continue
                existing = await self.get_by_code(model_code)
                if existing:
                    new_bindings = existing.get("channel_bindings", [])
                    has_binding = any(b["channel_code"] == channel_code for b in new_bindings)
                    if not has_binding:
                        new_bindings.append({
                            "channel_code": channel_code,
                            "channel_model_id": item.get("channel_model_id", model_code),
                            "priority": 1,
                            "status": "active"
                        })
                        await self.update(existing["id"], {"channel_bindings": new_bindings})
                        imported += 1
                    else:
                        skipped += 1
                    continue

                doc = {
                    "model_code": model_code,
                    "model_name": item.get("model_name", model_code),
                    "category": item.get("category", "text"),
                    "cover": item.get("cover", ""),
                    "description": item.get("description", ""),
                    "tags": item.get("tags", []),
                    "channel_bindings": [{
                        "channel_code": channel_code,
                        "channel_model_id": item.get("channel_model_id", model_code),
                        "priority": 1,
                        "status": "active"
                    }],
                    "param_schema": item.get("param_schema", {"fields": []}),
                    "status": "online",
                    "sort_order": 0,
                    "is_default": False,
                }
                await self.create(doc)
                imported += 1
            except Exception as e:
                failed += 1
                messages.append(f"{item.get('model_code')}: {str(e)}")

        return {
            "total": len(models_data),
            "imported": imported,
            "skipped": skipped,
            "failed": failed,
            "messages": messages
        }

    def _to_response(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(doc["_id"]),
            "model_code": doc["model_code"],
            "model_name": doc["model_name"],
            "category": doc["category"],
            "cover": doc.get("cover", ""),
            "description": doc.get("description", ""),
            "tags": doc.get("tags", []),
            "channel_bindings": doc.get("channel_bindings", []),
            "param_schema": doc.get("param_schema", {"fields": []}),
            "supported_inputs": doc.get("supported_inputs", {}),
            "status": doc["status"],
            "sort_order": doc.get("sort_order", 0),
            "is_default": doc.get("is_default", False),
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }

    def _to_public_item(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(doc["_id"]),
            "model_code": doc["model_code"],
            "model_name": doc["model_name"],
            "category": doc["category"],
            "cover": doc.get("cover", ""),
            "description": doc.get("description", ""),
            "tags": doc.get("tags", []),
            "param_schema": doc.get("param_schema", {"fields": []}),
            "supported_inputs": doc.get("supported_inputs", {}),
            "is_default": doc.get("is_default", False),
        }


_model_service = None


def get_model_service() -> ModelService:
    global _model_service
    if _model_service is None:
        _model_service = ModelService()
    return _model_service
