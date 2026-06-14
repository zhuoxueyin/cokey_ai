from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import json

from app.core.database import get_collection
from app.core.logging_config import get_logger
from app.core.utils import generate_task_id, generate_trace_id
from bson import ObjectId

logger = get_logger()


class TaskService:
    def __init__(self):
        self.collection = get_collection("tasks")

    async def create(self, model_code: str, category: str, params: Dict[str, Any],
                     session_id: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.utcnow()
        task_id = generate_task_id()
        trace_id = generate_trace_id()
        doc = {
            "task_id": task_id,
            "session_id": session_id,
            "model_code": model_code,
            "channel_code": None,
            "category": category,
            "params": params,
            "status": "pending",
            "result": None,
            "error_message": None,
            "duration_ms": None,
            "trace_id": trace_id,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)

        if session_id:
            from app.services.session_service import get_session_service
            await get_session_service().add_task(session_id, task_id)

        return self._to_response(doc)

    async def get_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"task_id": task_id})
        return self._to_response(doc) if doc else None

    async def update_status(self, task_id: str, status: str, result: Optional[Dict[str, Any]] = None,
                            error_message: Optional[str] = None, channel_code: Optional[str] = None,
                            duration_ms: Optional[int] = None) -> bool:
        update_data = {"status": status, "updated_at": datetime.utcnow()}
        if result is not None:
            update_data["result"] = result
        if error_message is not None:
            update_data["error_message"] = error_message
        if channel_code is not None:
            update_data["channel_code"] = channel_code
        if duration_ms is not None:
            update_data["duration_ms"] = duration_ms

        result_obj = await self.collection.update_one({"task_id": task_id}, {"$set": update_data})
        return result_obj.modified_count > 0

    async def list(self, page: int = 1, page_size: int = 20, session_id: Optional[str] = None,
                   model_code: Optional[str] = None, category: Optional[str] = None,
                   status: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
        query = {}
        if session_id:
            query["session_id"] = session_id
        if model_code:
            query["model_code"] = model_code
        if category:
            query["category"] = category
        if status:
            query["status"] = status
        cursor = self.collection.find(query).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
        total = await self.collection.count_documents(query)
        docs = []
        async for doc in cursor:
            docs.append(self._to_response(doc))
        return docs, total

    async def list_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"session_id": session_id}).sort("created_at", 1)
        docs = []
        async for doc in cursor:
            docs.append(self._to_response(doc))
        return docs

    async def get_stats(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
                        category: Optional[str] = None) -> Dict[str, Any]:
        query = {}
        if start_time:
            query["created_at"] = {"$gte": start_time}
        if end_time:
            if "created_at" in query:
                query["created_at"]["$lte"] = end_time
            else:
                query["created_at"] = {"$lte": end_time}
        if category:
            query["category"] = category

        total = await self.collection.count_documents(query)
        success_query = {**query, "status": "success"}
        failed_query = {**query, "status": "failed"}

        success_count = await self.collection.count_documents(success_query)
        failed_count = await self.collection.count_documents(failed_query)

        pipeline = [
            {"$match": query},
            {"$match": {"duration_ms": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": None, "avg_duration": {"$avg": "$duration_ms"}}}
        ]
        avg_result = await self.collection.aggregate(pipeline).to_list(length=1)
        avg_duration = avg_result[0]["avg_duration"] if avg_result else 0

        return {
            "total_tasks": total,
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": (success_count / total * 100) if total > 0 else 0,
            "avg_duration_ms": avg_duration,
        }

    def _to_response(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        params = doc.get("params", {})
        params_summary = ""
        if params.get("prompt"):
            params_summary = params["prompt"][:50]
        elif params.get("positive_prompt"):
            params_summary = params["positive_prompt"][:50]
        elif params:
            params_summary = f"参数: {len(params)}项"

        return {
            "id": str(doc["_id"]),
            "task_id": doc["task_id"],
            "session_id": doc.get("session_id"),
            "model_code": doc["model_code"],
            "channel_code": doc.get("channel_code"),
            "category": doc["category"],
            "status": doc["status"],
            "params": params,
            "params_summary": params_summary,
            "result": doc.get("result"),
            "error_message": doc.get("error_message"),
            "duration_ms": doc.get("duration_ms"),
            "trace_id": doc.get("trace_id"),
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }


_task_service = None


def get_task_service() -> TaskService:
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service
