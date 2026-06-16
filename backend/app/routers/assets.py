from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from typing import Optional

from app.core.response import success, error
from app.services.storage_service import get_storage_service
from app.services.asset_service import get_asset_service
from app.core.logging_config import get_logger

logger = get_logger()
router = APIRouter(prefix="/assets", tags=["资源管理"])


ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
MAX_IMAGE_SIZE = 20 * 1024 * 1024
MAX_FILE_SIZE = 100 * 1024 * 1024


def _get_extension(filename: str) -> str:
    import os
    _, ext = os.path.splitext(filename or "")
    return ext.lower()


@router.get("")
async def list_assets(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="资源类型：image/file/video"),
    source_type: Optional[str] = Query(None, description="来源：upload=用户上传, generated=AI生成"),
):
    """资源列表（分页）"""
    try:
        assets, total = await get_asset_service().list(
            page=page,
            page_size=page_size,
            category=category,
            source_type=source_type,
        )
        return success({
            "items": assets,
            "total": total,
            "page": page,
            "page_size": page_size,
        })
    except Exception as e:
        logger.error(f"获取资源列表失败: {e}")
        return error("internal_error", str(e))


@router.get("/{asset_id}")
async def get_asset(asset_id: str):
    """获取单个资源详情"""
    try:
        asset = await get_asset_service().get_by_id(asset_id)
        if not asset:
            return error("not_found", "资源不存在")
        return success(asset)
    except Exception as e:
        logger.error(f"获取资源详情失败: {e}")
        return error("internal_error", str(e))


@router.post("/upload")
async def upload_asset(
    file: UploadFile = File(...),
    category: str = Query("image", description="资源类型：image/file/video"),
    source_type: str = Query("upload", description="来源：upload=用户上传, generated=AI生成"),
):
    """上传新资源

    - 上传文件到 GitHub 仓库
    - 同时把元数据写入 MongoDB 的 assets 集合
    - 返回：{id, url, cdn_urls, file_name, file_size, ...}
    """
    try:
        content = await file.read()
        filename = file.filename or "file"
        content_type = file.content_type or "application/octet-stream"

        if len(content) == 0:
            return error("validation_error", "文件为空")
        if len(content) > MAX_FILE_SIZE:
            return error("file_too_large", f"文件大小超过{MAX_FILE_SIZE // (1024*1024)}MB限制")

        # 图片单独校验
        if category == "image":
            ext = _get_extension(filename)
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                return error("invalid_file_type", f"不支持的图片格式: {ext}（支持: png, jpg, jpeg, gif, webp, bmp）")
            if len(content) > MAX_IMAGE_SIZE:
                return error("file_too_large", "图片大小超过20MB限制")

        storage = get_storage_service()
        cdn_url, file_path = await storage.upload_file(
            content, filename, category, content_type
        )
        cdn_urls = storage.get_all_cdn_urls(file_path)

        asset = await get_asset_service().create(
            file_name=filename,
            file_path=file_path,
            url=cdn_url,
            cdn_urls=cdn_urls,
            file_size=len(content),
            content_type=content_type,
            category=category,
            source_type=source_type,
        )

        logger.info(f"资源上传成功: {filename} -> {cdn_url}")
        return success(asset)

    except Exception as e:
        logger.error(f"资源上传失败: {e}")
        return error("internal_error", str(e))


@router.delete("/{asset_id}")
async def delete_asset(asset_id: str):
    """删除资源

    仅删除 MongoDB 中的元数据记录，GitHub 文件保持不变（因为被其他地方引用）。
    """
    try:
        ok = await get_asset_service().delete(asset_id)
        if not ok:
            return error("not_found", "资源不存在")
        return success({"id": asset_id, "deleted": True})
    except Exception as e:
        logger.error(f"删除资源失败: {e}")
        return error("internal_error", str(e))
