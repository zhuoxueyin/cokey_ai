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
                     session_id: Optional[str] = None, user_id: Optional[str] = None,
                     canvas_project_id: Optional[str] = None,
                     canvas_node_id: Optional[str] = None,
                     canvas_node_title: Optional[str] = None,
                     canvas_node_type: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.utcnow()
        task_id = generate_task_id()
        trace_id = generate_trace_id()
        doc = {
            "task_id": task_id,
            "session_id": session_id,
            "user_id": user_id,           # 新增：用户ID，用于多用户隔离
            "model_code": model_code,
            "channel_code": None,
            "category": category,
            "params": params,
            "status": "pending",
            "result": None,
            "error_message": None,
            "duration_ms": None,
            "trace_id": trace_id,
            "channel_request": None,      # 渠道请求参数
            "channel_response": None,     # 渠道响应（视频类型包含创建和查询两次响应）
            "external_task_id": None,     # 第三方服务返回的任务ID（用于服务器重启后恢复状态）
            "canvas_project_id": canvas_project_id,
            "canvas_node_id": canvas_node_id,
            "canvas_node_title": canvas_node_title,
            "canvas_node_type": canvas_node_type,
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

    def _truncate_large_data(self, data: Any, max_size: int = 1024 * 1024) -> Any:
        """截断过大的数据，防止MongoDB文档超过16MB限制"""
        if isinstance(data, dict):
            return {k: self._truncate_large_data(v, max_size) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._truncate_large_data(item, max_size) for item in data]
        elif isinstance(data, str):
            # 检查是否是base64图片数据（通常以data:image开头或包含大量base64字符）
            is_base64_image = data.startswith('data:image/') or (len(data) > 1000 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in data[:1000]))
            if is_base64_image:
                # 对于图片数据，保留合理大小（约500KB）
                max_image_size = 512 * 1024
                if len(data) > max_image_size:
                    return data[:max_image_size] + f" [TRUNCATED_IMAGE: {len(data) - max_image_size} chars]"
                return data
            if len(data) > max_size:
                return data[:max_size] + f" [TRUNCATED: {len(data) - max_size} chars]"
            return data
        return data

    async def update_status(self, task_id: str, status: str, result: Optional[Dict[str, Any]] = None,
                            error_message: Optional[str] = None, channel_code: Optional[str] = None,
                            duration_ms: Optional[int] = None, channel_request: Optional[Dict[str, Any]] = None,
                            channel_response: Optional[Dict[str, Any]] = None,
                            external_task_id: Optional[str] = None) -> bool:
        update_data = {"status": status, "updated_at": datetime.utcnow()}
        if result is not None:
            # 限制result大小，防止文档过大
            update_data["result"] = self._truncate_large_data(result, 5 * 1024 * 1024)
        if error_message is not None:
            update_data["error_message"] = error_message[:1000]  # 限制错误消息长度
        if channel_code is not None:
            update_data["channel_code"] = channel_code
        if duration_ms is not None:
            update_data["duration_ms"] = duration_ms
        if channel_request is not None:
            # 限制channel_request大小
            update_data["channel_request"] = self._truncate_large_data(channel_request, 1 * 1024 * 1024)
        if channel_response is not None:
            # 限制channel_response大小（主要问题来源）
            update_data["channel_response"] = self._truncate_large_data(channel_response, 5 * 1024 * 1024)
        if external_task_id is not None:
            update_data["external_task_id"] = external_task_id

        result_obj = await self.collection.update_one({"task_id": task_id}, {"$set": update_data})
        return result_obj.modified_count > 0

    async def patch_channel_request(
        self,
        task_id: str,
        channel_request: Dict[str, Any],
        channel_code: Optional[str] = None,
    ) -> bool:
        """仅更新渠道入参（在 HTTP 发出前写入，不等待结果）"""
        update_data: Dict[str, Any] = {
            "channel_request": self._truncate_large_data(channel_request, 1 * 1024 * 1024),
            "updated_at": datetime.utcnow(),
        }
        if channel_code is not None:
            update_data["channel_code"] = channel_code
        result_obj = await self.collection.update_one({"task_id": task_id}, {"$set": update_data})
        return result_obj.modified_count > 0

    async def patch_channel_response(
        self,
        task_id: str,
        channel_response: Dict[str, Any],
    ) -> bool:
        """仅更新渠道出参"""
        update_data = {
            "channel_response": self._truncate_large_data(channel_response, 5 * 1024 * 1024),
            "updated_at": datetime.utcnow(),
        }
        result_obj = await self.collection.update_one({"task_id": task_id}, {"$set": update_data})
        return result_obj.modified_count > 0

    async def get_by_external_task_id(self, external_task_id: str) -> Optional[Dict[str, Any]]:
        """通过外部任务ID查询任务（用于服务器重启后恢复状态）"""
        doc = await self.collection.find_one({"external_task_id": external_task_id})
        return self._to_response(doc) if doc else None

    async def get_processing_tasks(self) -> List[Dict[str, Any]]:
        """获取所有processing状态的任务（用于服务器重启后恢复）"""
        cursor = self.collection.find({"status": "processing"})
        tasks = []
        async for doc in cursor:
            tasks.append(self._to_response(doc))
        return tasks

    async def list(self, page: int = 1, page_size: int = 20, session_id: Optional[str] = None,
                   task_id: Optional[str] = None, trace_id: Optional[str] = None,
                   model_code: Optional[str] = None, channel_code: Optional[str] = None,
                   category: Optional[str] = None,
                   status: Optional[str] = None, user_id: Optional[str] = None,
                   time_range: str = "6h",
                   sort_by: str = "created_at", sort_order: int = -1) -> Tuple[List[Dict[str, Any]], int]:
        query = {}
        if task_id:
            query["task_id"] = task_id
        if trace_id:
            query["trace_id"] = trace_id
        if user_id:
            # 支持查询有user_id的任务，以及兼容旧数据（没有user_id的任务）
            query["$or"] = [
                {"user_id": user_id},
                {"user_id": {"$exists": False}},
                {"user_id": None}
            ]
        if session_id:
            query["session_id"] = session_id
        if model_code:
            query["model_code"] = model_code
        if channel_code:
            query["channel_code"] = channel_code
        if category:
            query["category"] = category
        if status:
            query["status"] = status
        
        # 时间范围筛选
        if time_range and time_range != "all":
            from datetime import timedelta
            now = datetime.utcnow()
            time_map = {
                "1h": timedelta(hours=1),
                "6h": timedelta(hours=6),
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30)
            }
            delta = time_map.get(time_range, timedelta(hours=6))  # 默认6小时
            query["created_at"] = {"$gte": now - delta}
        
        # 默认降序排序（最新的在前面），支持自定义排序字段和顺序
        cursor = self.collection.find(query).sort(sort_by, sort_order).skip((page - 1) * page_size).limit(page_size)
        total = await self.collection.count_documents(query)
        docs = []
        async for doc in cursor:
            docs.append(self._to_response(doc))
        return docs, total

    async def list_by_user(self, user_id: str, page: int = 1, page_size: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """按用户ID查询任务列表"""
        return await self.list(page=page, page_size=page_size, user_id=user_id)

    async def list_by_session(self, session_id: str, category: str = None, time_range: int = None) -> List[Dict[str, Any]]:
        # AI创作流使用升序排序（最早的在前面，最新的在底部），符合聊天对话习惯
        # 与任务管理的降序排序（最新的在前面）相互隔离
        from pymongo import ASCENDING
        
        query = {"session_id": session_id}
        
        # 类型筛选
        if category and category != 'all':
            query["category"] = category
        
        # 时间范围筛选（单位：小时；0=全部时间，默认最近1天=24小时）
        if time_range is None:
            time_range = 24
        if time_range and time_range > 0:
            from datetime import datetime, timedelta
            start_time = datetime.utcnow() - timedelta(hours=time_range)
            query["created_at"] = {"$gte": start_time}
        
        cursor = self.collection.find(query).sort("created_at", ASCENDING)
        docs = []
        async for doc in cursor:
            docs.append(self._to_response(doc))
        return docs

    async def cancel_all_running(self) -> Dict[str, Any]:
        """将所有 pending 和 processing 的任务标记为 failed（已取消）"""
        now = datetime.utcnow()
        query = {"status": {"$in": ["pending", "processing"]}}
        update_data = {
            "status": "failed",
            "error_message": "用户手动停止",
            "updated_at": now
        }
        result = await self.collection.update_many(query, {"$set": update_data})
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消单个任务（将 pending/processing 任务标记为 failed）"""
        now = datetime.utcnow()
        query = {"task_id": task_id, "status": {"$in": ["pending", "processing"]}}
        update_data = {
            "status": "failed",
            "error_message": "用户手动停止",
            "updated_at": now
        }
        result = await self.collection.update_one(query, {"$set": update_data})
        return result.modified_count > 0

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

        statuses = ["success", "failed", "pending", "processing"]
        status_counts: Dict[str, int] = {}
        for s in statuses:
            status_counts[s] = await self.collection.count_documents({**query, "status": s})

        success_count = status_counts["success"]
        failed_count = status_counts["failed"]
        pending_count = status_counts["pending"]
        processing_count = status_counts["processing"]

        completed = success_count + failed_count
        success_rate = (success_count / completed * 100) if completed > 0 else 0

        pipeline = [
            {"$match": {**query, "duration_ms": {"$exists": True, "$ne": None, "$gt": 0}}},
            {"$group": {"_id": None, "avg_duration": {"$avg": "$duration_ms"}}}
        ]
        avg_result = await self.collection.aggregate(pipeline).to_list(length=1)
        avg_duration = float(avg_result[0]["avg_duration"]) if avg_result else 0

        category_counts = {}
        for cat in ["text", "image", "video"]:
            category_counts[cat] = await self.collection.count_documents({**query, "category": cat})

        return {
            "total_tasks": total,
            "success_count": success_count,
            "failed_count": failed_count,
            "pending_count": pending_count,
            "processing_count": processing_count,
            "success_rate": success_rate,
            "avg_duration_ms": round(avg_duration, 2),
            "category_breakdown": category_counts,
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
            "external_task_id": doc.get("external_task_id"),
            "channel_request": doc.get("channel_request"),      # 渠道请求参数
            "channel_response": doc.get("channel_response"),    # 渠道响应
            "canvas_project_id": doc.get("canvas_project_id"),
            "canvas_node_id": doc.get("canvas_node_id"),
            "canvas_node_title": doc.get("canvas_node_title"),
            "canvas_node_type": doc.get("canvas_node_type"),
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        }


_task_service = None


def get_task_service() -> TaskService:
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service
