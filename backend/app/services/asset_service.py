from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from app.core.database import get_collection
from app.core.logging_config import get_logger
from app.core.cdn import resolve_asset_cdn_url
from bson import ObjectId

logger = get_logger()


def _file_path_from_cdn_url(cdn_url: str) -> tuple[str, List[str]]:
    """从 CDN URL 反推 GitHub file_path 与全部 CDN 镜像。"""
    from app.services.storage_service import get_storage_service

    if not cdn_url:
        return "", []
    storage = get_storage_service()
    file_path = ""
    cdn_urls = [cdn_url]
    if storage.enabled and "/gh/" in cdn_url:
        try:
            suffix = f"@{storage.branch}/"
            pos = cdn_url.find(suffix)
            if pos > 0:
                file_path = cdn_url[pos + len(suffix) :]
                cdn_urls = storage.get_all_cdn_urls(file_path)
        except Exception:
            pass
    return file_path, cdn_urls


async def register_generated_assets_from_result(
    result_data: Dict[str, Any],
    *,
    task_id: str,
    category: Optional[str] = None,
    trace_id: str = "",
    skip_existing: bool = True,
) -> int:
    """将 AI 生成结果中的图片/视频写入 assets 集合（source_type=generated）。"""
    if not result_data:
        return 0

    svc = get_asset_service()
    res_type = result_data.get("type") or category or "image"
    registered = 0

    async def _already_exists(url: str) -> bool:
        if not skip_existing or not url:
            return bool(url)
        doc = await svc.collection.find_one(
            {
                "source_type": "generated",
                "$or": [{"url": url}, {"cdn_urls": url}],
            }
        )
        return doc is not None

    if res_type == "image":
        from app.adapters.weelinking import _ensure_cdn_url
        from app.core.cdn import is_cdn_url

        images = result_data.get("images") or []
        for idx, img in enumerate(images):
            try:
                img_url = img.get("url") if isinstance(img, dict) else str(img)
                if not img_url:
                    continue
                cdn_url = img_url
                if isinstance(img, dict) and img.get("cdn_url"):
                    cdn_url = str(img["cdn_url"])
                elif not is_cdn_url(cdn_url):
                    cdn_url = await _ensure_cdn_url(img_url, trace_id)
                if await _already_exists(cdn_url or img_url):
                    continue
                file_path, cdn_urls = _file_path_from_cdn_url(cdn_url or img_url)
                await svc.create(
                    file_name=f"generated_{task_id}_{idx}.png",
                    file_path=file_path,
                    url=cdn_url or img_url,
                    cdn_urls=cdn_urls or [cdn_url or img_url],
                    file_size=0,
                    content_type="image/png",
                    category="image",
                    source_type="generated",
                )
                registered += 1
            except Exception as e:
                logger.warning(f"记录生成图片到 assets 失败 task={task_id} idx={idx}: {e}")
    elif res_type == "video":
        videos = result_data.get("videos") or []
        for idx, vid in enumerate(videos):
            try:
                vid_url = vid.get("url") if isinstance(vid, dict) else str(vid)
                if not vid_url:
                    continue
                if await _already_exists(vid_url):
                    continue
                await svc.create(
                    file_name=f"generated_{task_id}_{idx}.mp4",
                    file_path="",
                    url=vid_url,
                    cdn_urls=[vid_url],
                    file_size=0,
                    content_type="video/mp4",
                    category="video",
                    source_type="generated",
                )
                registered += 1
            except Exception as e:
                logger.warning(f"记录生成视频到 assets 失败 task={task_id} idx={idx}: {e}")

    return registered


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
