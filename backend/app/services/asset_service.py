from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from app.core.database import get_collection
from app.core.logging_config import get_logger
from app.core.cdn import resolve_asset_cdn_url
from bson import ObjectId

logger = get_logger()


class AssetService:
    """资源管理服务

    所有上传的图片/文件都在这里记录，方便管理、复用、选择。
    存储在 MongoDB 的 `assets` 集合中。
    """

    def __init__(self):
        self.collection = get_collection("assets")

    async def create(
        self,
        file_name: str,
        file_path: str,
        url: str,
        cdn_urls: List[str],
        file_size: int,
        content_type: str,
        category: str = "image",
        source_type: str = "upload",
    ) -> Dict[str, Any]:
        """新建一条资源记录

        Args:
            source_type: 'upload' = 用户上传, 'generated' = AI生成
        """
        now = datetime.utcnow()
        doc = {
            "file_name": file_name,
            "file_path": file_path,
            "url": url,
            "cdn_urls": cdn_urls,
            "file_size": file_size,
            "content_type": content_type,
            "category": category,
            "source_type": source_type,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return self._to_response(doc)

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        source_type: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """资源列表（按创建时间倒序）"""
        query: Dict[str, Any] = {}
        if category:
            query["category"] = category
        if source_type:
            # 兼容老数据：source_type 不存在于老数据时，默认视为 upload
            if source_type == "upload":
                query["$or"] = [
                    {"source_type": "upload"},
                    {"source_type": {"$exists": False}}
                ]
            else:
                query["source_type"] = source_type
        cursor = self.collection.find(query).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
        total = await self.collection.count_documents(query)
        docs: List[Dict[str, Any]] = []
        async for doc in cursor:
            docs.append(self._to_response(doc))
        return docs, total

    async def get_by_id(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """按 ID 获取资源详情"""
        if not ObjectId.is_valid(asset_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(asset_id)})
        return self._to_response(doc) if doc else None

    async def delete(self, asset_id: str) -> bool:
        """删除资源（仅删除 MongoDB 记录，GitHub 文件保持不变）"""
        if not ObjectId.is_valid(asset_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(asset_id)})
        return result.deleted_count > 0

    def _to_response(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        url = doc.get("url", "")
        cdn_urls = doc.get("cdn_urls", [])
        file_path = doc.get("file_path", "")
        resolved = resolve_asset_cdn_url(url, cdn_urls, file_path)
        return {
            "id": str(doc["_id"]),
            "file_name": doc.get("file_name", ""),
            "file_path": file_path,
            "url": url,
            "cdn_urls": cdn_urls,
            "resolved_cdn_url": resolved,
            "cdn_ready": bool(resolved),
            "file_size": doc.get("file_size", 0),
            "content_type": doc.get("content_type", ""),
            "category": doc.get("category", "image"),
            "source_type": doc.get("source_type", "upload"),
            "created_at": doc.get("created_at"),
            "updated_at": doc.get("updated_at"),
        }


_asset_service = None


def get_asset_service() -> AssetService:
    global _asset_service
    if _asset_service is None:
        _asset_service = AssetService()
    return _asset_service
