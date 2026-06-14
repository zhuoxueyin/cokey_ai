from fastapi import APIRouter, File, UploadFile, HTTPException
from app.core.response import success, error
from app.services.storage_service import get_storage_service
from app.core.logging_config import get_logger

logger = get_logger()
router = APIRouter(prefix="/upload", tags=["用户-上传"])


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    try:
        content = await file.read()
        content_type = file.content_type or "image/png"
        filename = file.filename or "upload.png"

        if len(content) == 0:
            return error("validation_error", "文件为空")
        if len(content) > 20 * 1024 * 1024:
            return error("file_too_large", "文件大小超过20MB限制")

        url = await get_storage_service().upload_reference_image(content, filename, content_type)
        return success({
            "url": url,
            "file_size": len(content),
            "content_type": content_type,
            "filename": filename
        })
    except Exception as e:
        logger.error(f"上传图片失败: {e}")
        return error("internal_error", str(e))


@router.post("/file")
async def upload_generic(file: UploadFile = File(...)):
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
