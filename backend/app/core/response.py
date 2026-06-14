from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime


class ErrorResponse(BaseModel):
    code: str
    message: str


class SuccessResponse(BaseModel):
    code: str = "success"
    message: str = "操作成功"
    data: Optional[Any] = None


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    code: str = "success"
    message: str = "操作成功"
    data: Any
    total: int
    page: int
    page_size: int
    total_pages: int


ERROR_CODES = {
    "success": "操作成功",
    "validation_error": "参数校验失败",
    "unauthorized": "未授权访问",
    "forbidden": "没有权限",
    "not_found": "资源不存在",
    "internal_error": "系统内部错误",
    "channel_error": "渠道调用失败",
    "model_not_found": "模型不存在",
    "model_offline": "模型已下架",
    "task_not_found": "任务不存在",
    "task_failed": "任务执行失败",
    "rate_limit_exceeded": "请求过于频繁，请稍后再试",
    "content_violation": "内容不符合规范",
    "timeout": "生成超时，请稍后重试",
    "service_unavailable": "服务暂不可用",
    "file_too_large": "文件大小超出限制",
    "invalid_file_format": "文件格式不支持",
}


def success(data: Any = None, message: str = None) -> Dict[str, Any]:
    return {
        "code": "success",
        "message": message or ERROR_CODES["success"],
        "data": data,
    }


def paginated(data: Any, total: int, page: int, page_size: int) -> Dict[str, Any]:
    return {
        "code": "success",
        "message": ERROR_CODES["success"],
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
    }


def error(code: str, message: str = None) -> Dict[str, Any]:
    return {
        "code": code,
        "message": message or ERROR_CODES.get(code, "未知错误"),
    }
