"""任务链路追踪日志 — 记录从前端入参到渠道调用的关键步骤"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.core.database import get_collection
from app.core.logging_config import get_logger

logger = get_logger()

_TIME_RANGE_MAP = {
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


class TraceLogService:
    def __init__(self):
        self.collection = get_collection("trace_logs")

    def _truncate(self, data: Any, max_str: int = 200_000) -> Any:
        if isinstance(data, dict):
            return {k: self._truncate(v, max_str) for k, v in data.items()}
        if isinstance(data, list):
            return [self._truncate(item, max_str) for item in data[:50]]
        if isinstance(data, str):
            if data.startswith("data:image/") or (
                len(data) > 1000
                and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in data[:500])
            ):
                return f"[BASE64_IMAGE len={len(data)}]"
            if len(data) > max_str:
                return data[:max_str] + f" [TRUNCATED {len(data) - max_str} chars]"
            return data
        return data

    async def ensure_log(
        self,
        trace_id: str,
        *,
        task_id: Optional[str] = None,
        model_code: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        now = datetime.utcnow()
        # 同一字段不能同时出现在 $setOnInsert 与 $set，否则 MongoDB 报 code 40 冲突
        meta_updates = {
            k: v
            for k, v in {
                "task_id": task_id,
                "model_code": model_code,
                "category": category,
                "user_id": user_id,
                "session_id": session_id,
            }.items()
            if v is not None
        }
        await self.collection.update_one(
            {"trace_id": trace_id},
            {
                "$setOnInsert": {
                    "trace_id": trace_id,
                    "log_id": trace_id,
                    "status": "processing",
                    "steps": [],
                    "channel_attempts": [],
                    "created_at": now,
                },
                "$set": {
                    "updated_at": now,
                    **meta_updates,
                },
            },
            upsert=True,
        )

    async def append_step(
        self,
        trace_id: str,
        step: str,
        data: Optional[Dict[str, Any]] = None,
        *,
        level: str = "info",
    ) -> None:
        if not trace_id:
            return
        entry = {
            "step": step,
            "level": level,
            "timestamp": datetime.utcnow().isoformat(),
            "data": self._truncate(data or {}),
        }
        await self.collection.update_one(
            {"trace_id": trace_id},
            {
                "$push": {"steps": entry},
                "$set": {"updated_at": datetime.utcnow()},
            },
            upsert=True,
        )

    async def append_channel_attempt(
        self,
        trace_id: str,
        attempt: Dict[str, Any],
    ) -> None:
        if not trace_id:
            return
        await self.collection.update_one(
            {"trace_id": trace_id},
            {
                "$push": {"channel_attempts": self._truncate(attempt)},
                "$set": {"updated_at": datetime.utcnow()},
            },
            upsert=True,
        )

    async def finalize(
        self,
        trace_id: str,
        status: str,
        *,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        channel_code: Optional[str] = None,
    ) -> None:
        if not trace_id:
            return
        update: Dict[str, Any] = {
            "status": status,
            "updated_at": datetime.utcnow(),
        }
        if duration_ms is not None:
            update["duration_ms"] = duration_ms
        if error_message is not None:
            update["error_message"] = error_message[:2000]
        if channel_code is not None:
            update["channel_code"] = channel_code
        await self.collection.update_one({"trace_id": trace_id}, {"$set": update})

    async def get_by_trace_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"trace_id": trace_id})
        return self._to_response(doc) if doc else None

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        trace_id: Optional[str] = None,
        task_id: Optional[str] = None,
        model_code: Optional[str] = None,
        channel_code: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        time_range: str = "24h",
    ) -> Tuple[List[Dict[str, Any]], int]:
        query: Dict[str, Any] = {}
        if trace_id:
            query["trace_id"] = trace_id
        if task_id:
            query["task_id"] = task_id
        if model_code:
            query["model_code"] = model_code
        if channel_code:
            query["channel_code"] = channel_code
        if category:
            query["category"] = category
        if status:
            query["status"] = status
        if time_range != "all":
            delta = _TIME_RANGE_MAP.get(time_range, _TIME_RANGE_MAP["24h"])
            query["created_at"] = {"$gte": datetime.utcnow() - delta}

        total = await self.collection.count_documents(query)
        skip = (page - 1) * page_size
        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(page_size)
        )
        items = [self._to_response(doc) async for doc in cursor]
        return items, total

    def _to_response(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "log_id": doc.get("log_id") or doc.get("trace_id"),
            "trace_id": doc.get("trace_id"),
            "task_id": doc.get("task_id"),
            "session_id": doc.get("session_id"),
            "model_code": doc.get("model_code"),
            "category": doc.get("category"),
            "user_id": doc.get("user_id"),
            "status": doc.get("status", "processing"),
            "channel_code": doc.get("channel_code"),
            "duration_ms": doc.get("duration_ms"),
            "error_message": doc.get("error_message"),
            "steps": doc.get("steps") or [],
            "channel_attempts": doc.get("channel_attempts") or [],
            "step_count": len(doc.get("steps") or []),
            "created_at": doc.get("created_at"),
            "updated_at": doc.get("updated_at"),
        }


_trace_log_service: Optional[TraceLogService] = None


def get_trace_log_service() -> TraceLogService:
    global _trace_log_service
    if _trace_log_service is None:
        _trace_log_service = TraceLogService()
    return _trace_log_service
