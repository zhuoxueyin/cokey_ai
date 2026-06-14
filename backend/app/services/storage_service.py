import base64
import httpx
from datetime import datetime
from typing import Optional, Tuple
from pathlib import PurePosixPath
import uuid

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger()

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".avi"}
MAX_IMAGE_SIZE = 20 * 1024 * 1024
MAX_VIDEO_SIZE = 100 * 1024 * 1024


class GithubStorageService:
    def __init__(self):
        self.token = settings.github_token
        self.username = settings.github_username
        self.repo = settings.github_repo
        self.branch = settings.github_branch
        self.api_base = "https://api.github.com"
        self.cdn_base = "https://cdn.jsdelivr.net/gh"
        self.enabled = bool(self.token and self.username and self.repo)
        if not self.enabled:
            logger.warning("GitHub存储服务未配置（缺少token/username/repo），文件上传功能将不可用")

    def _get_file_extension(self, filename: str) -> str:
        import os
        _, ext = os.path.splitext(filename)
        return ext.lower() if ext else ".bin"

    def _generate_filename(self, extension: str) -> str:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{uuid.uuid4().hex}_{ts}{extension}"

    def _get_storage_path(self, category: str, filename: str) -> str:
        if category == "reference":
            return f"upload/reference/{filename}"
        elif category == "image":
            return f"output/image/{filename}"
        elif category == "video":
            return f"output/video/{filename}"
        else:
            return f"upload/other/{filename}"

    def get_cdn_url(self, file_path: str) -> str:
        return f"{self.cdn_base}/{self.username}/{self.repo}@{self.branch}/{file_path}"

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        category: str,
        content_type: str = "application/octet-stream"
    ) -> Tuple[str, str]:
        if not self.enabled:
            raise Exception("GitHub存储服务未配置")

        extension = self._get_file_extension(filename)
        gen_filename = self._generate_filename(extension)
        file_path = self._get_storage_path(category, gen_filename)

        encoded_content = base64.b64encode(file_content).decode("utf-8")

        url = f"{self.api_base}/repos/{self.username}/{self.repo}/contents/{file_path}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        }
        payload = {
            "message": f"upload {category}: {gen_filename}",
            "content": encoded_content,
            "branch": self.branch,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.put(url, json=payload, headers=headers)
            if response.status_code not in (201, 200):
                error_msg = response.json().get("message", "上传失败")
                logger.error(f"GitHub上传失败: {response.status_code} - {error_msg}")
                raise Exception(f"文件上传失败: {error_msg}")

        cdn_url = self.get_cdn_url(file_path)
        logger.info(f"文件上传成功: {file_path} -> {cdn_url}")
        return cdn_url, file_path

    async def upload_reference_image(self, file_content: bytes, filename: str, content_type: str) -> str:
        ext = self._get_file_extension(filename)
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise Exception(f"不支持的图片格式: {ext}")
        if len(file_content) > MAX_IMAGE_SIZE:
            raise Exception("图片大小超过20MB限制")
        cdn_url, _ = await self.upload_file(file_content, filename, "reference", content_type)
        return cdn_url

    async def upload_generated_image(self, file_content: bytes, filename: str, content_type: str) -> str:
        cdn_url, _ = await self.upload_file(file_content, filename, "image", content_type)
        return cdn_url

    async def upload_generated_video(self, file_content: bytes, filename: str, content_type: str) -> str:
        ext = self._get_file_extension(filename)
        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            raise Exception(f"不支持的视频格式: {ext}")
        if len(file_content) > MAX_VIDEO_SIZE:
            raise Exception("视频大小超过100MB限制")
        cdn_url, _ = await self.upload_file(file_content, filename, "video", content_type)
        return cdn_url


_storage_service = None


def get_storage_service() -> GithubStorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = GithubStorageService()
    return _storage_service
