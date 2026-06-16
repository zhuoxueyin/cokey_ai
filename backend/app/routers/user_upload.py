from fastapi import APIRouter, File, UploadFile, HTTPException
from app.core.response import success, error
from app.services.storage_service import get_storage_service
from app.services.asset_service import get_asset_service
from app.core.logging_config import get_logger

logger = get_logger()
router = APIRouter(prefix="/upload", tags=["用户-上传"])


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    """上传图片

    - 图片上传到 GitHub 仓库的 assets/images/ 目录
    - 同时把元数据写入 MongoDB 的 assets 集合（供资源管理页面查询）
    """
    try:
        content = await file.read()
        content_type = file.content_type or "image/png"
        filename = file.filename or "upload.png"

        if len(content) == 0:
            return error("validation_error", "文件为空")
        if len(content) > 20 * 1024 * 1024:
            return error("file_too_large", "文件大小超过20MB限制")

        storage = get_storage_service()
        url = await storage.upload_reference_image(content, filename, content_type)

        # 从 URL 反推 file_path（用于 cdn_urls 生成）
        file_path = ""
        # URL 格式为 https://cdn.jsdelivr.net/gh/user/repo@branch/assets/images/xxx.png
        try:
            # 提取 @branch/ 之后的部分
            suffix = f"@{storage.branch}/"
            idx = url.find(suffix)
            if idx > 0:
                file_path = url[idx + len(suffix):]
        except Exception:
            file_path = ""

        cdn_urls = storage.get_all_cdn_urls(file_path) if file_path else [url]

        # 写入 assets 集合，方便在资源管理页面选择
        try:
            await get_asset_service().create(
                file_name=filename,
                file_path=file_path,
                url=url,
                cdn_urls=cdn_urls,
                file_size=len(content),
                content_type=content_type,
                category="image",
                source_type="upload",
            )
        except Exception as _e:
            logger.warning(f"写入 assets 集合失败（不影响返回结果）: {_e}")

        return success({
            "url": url,
            "cdn_urls": cdn_urls,
            "file_size": len(content),
            "content_type": content_type,
            "filename": filename,
        })
    except Exception as e:
        logger.error(f"上传图片失败: {e}")
        return error("internal_error", str(e))


@router.post("/file")
async def upload_generic(file: UploadFile = File(...)):
    """上传通用文件"""
    try:
        content = await file.read()
        content_type = file.content_type or "application/octet-stream"
        filename = file.filename or "file"

        if len(content) == 0:
            return error("validation_error", "文件为空")
        if len(content) > 100 * 1024 * 1024:
            return error("file_too_large", "文件大小超过100MB限制")

        url, file_path = await get_storage_service().upload_file(content, filename, "reference", content_type)
        return success({
            "url": url,
            "file_path": file_path,
            "file_size": len(content),
            "content_type": content_type,
            "filename": filename
        })
    except Exception as e:
        logger.error(f"上传文件失败: {e}")
        return error("internal_error", str(e))
