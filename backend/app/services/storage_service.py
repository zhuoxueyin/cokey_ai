import base64
import hashlib
import time
from datetime import datetime
from typing import Tuple, Optional

import httpx

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger()

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".avi"}
MAX_IMAGE_SIZE = 20 * 1024 * 1024
MAX_VIDEO_SIZE = 100 * 1024 * 1024


class GitHubStorageService:
    """GitHub 仓库 + jsDelivr CDN 图片/文件存储服务

    文件存储在 GitHub 仓库的 assets/ 目录下，通过 jsDelivr 国内镜像 CDN 提供访问。
    """

    def __init__(self):
        self.token = settings.github_token
        self.repo = settings.github_repo or "zhuoxueyin/cokey_ai"
        self.branch = settings.github_branch or "main"
        self.api_base = "https://api.github.com"
        self.cdn_base = settings.github_cdn_prefix or "https://cdn.jsdmirror.com/gh"

        has_token = bool(self.token) and not self.token.startswith(("your-", "xxx", "PLACEHOLDER"))
        self.enabled = has_token and bool(self.repo)

        token_display = self.token[:8] + "..." if has_token and self.token else "(未设置)"
        logger.info(
            "GitHub存储服务初始化: "
            f"repo={self.repo}, branch={self.branch}, "
            f"cdn={self.cdn_base}, token={token_display}, "
            f"enabled={'YES' if self.enabled else 'NO'}"
        )

        if not self.enabled:
            logger.warning(
                "\n"
                "============================================================\n"
                "  GitHub存储服务未启用：请在 backend/.env 中配置 GITHUB_TOKEN\n"
                "  1. 访问 https://github.com/settings/tokens 生成 PAT\n"
                "  2. 将 token 填入 backend/.env 的 GITHUB_TOKEN= 行\n"
                "  3. 重启后端服务（先 stop 再 start）\n"
                "============================================================"
            )

    def _get_file_extension(self, filename: str) -> str:
        import os
        _, ext = os.path.splitext(filename)
        return ext.lower() if ext else ".bin"

    def _generate_path(self, category: str, filename: str) -> str:
        """生成 assets 目录下的存储路径"""
        ts = datetime.now().strftime("%Y%m%d")
        unique_id = hashlib.md5(f"{filename}{time.time()}".encode()).hexdigest()[:8]
        ext = self._get_file_extension(filename)
        return f"assets/{category}/{ts}/{unique_id}{ext}"

    def get_cdn_url(self, file_path: str) -> str:
        """获取主 CDN 访问地址（优先用 jsdmirror，国内最稳定）"""
        return self.get_all_cdn_urls(file_path)[0]

    def get_all_cdn_urls(self, file_path: str) -> list[str]:
        """获取所有 CDN 访问地址（按优先级排序，供前端回退使用）"""
        path = f"{self.repo}@{self.branch}/{file_path}"
        return [
            f"https://cdn.jsdmirror.com/gh/{path}",
            f"https://fastly.jsdelivr.net/gh/{path}",
            f"https://cdn.jsdelivr.net/gh/{path}",
            f"https://ghproxy.net/https://raw.githubusercontent.com/{self.repo}/{self.branch}/{file_path}",
            f"https://raw.githubusercontent.com/{self.repo}/{self.branch}/{file_path}",
        ]

    async def _upload_to_github(
        self,
        file_path: str,
        file_content: bytes,
        timeout: float = 60.0,
    ) -> str:
        """通过 GitHub API 上传文件到仓库

        Args:
            file_path: 仓库内的相对路径（如 assets/image/20260615/abc123.png）
            file_content: 文件二进制数据

        Returns:
            jsDelivr CDN 访问 URL

        Raises:
            Exception: 上传失败时抛出
        """
        if not self.enabled:
            raise Exception("GitHub存储服务未配置：请在 .env 中设置 GITHUB_TOKEN 和 GITHUB_REPO")

        encoded_content = base64.b64encode(file_content).decode("utf-8")
        url = f"{self.api_base}/repos/{self.repo}/contents/{file_path}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        }
        payload = {
            "message": f"upload: {file_path}",
            "content": encoded_content,
            "branch": self.branch,
        }

        last_error: Optional[Exception] = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.put(url, json=payload, headers=headers)

                if response.status_code in (201, 200):
                    cdn_url = self.get_cdn_url(file_path)
                    logger.info(f"文件上传成功: {file_path} -> {cdn_url}")
                    return cdn_url

                if response.status_code == 422:
                    raise Exception(f"文件已存在或无法上传: {response.json().get('message', 'unknown')}")

                error_msg = response.json().get("message", f"HTTP {response.status_code}")
                logger.warning(f"GitHub上传失败({attempt + 1}/3): {response.status_code} - {error_msg}")

                if response.status_code == 429 or response.status_code >= 500:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue

                raise Exception(f"文件上传失败: {error_msg}")

            except httpx.TimeoutException:
                if attempt < 2:
                    wait_time = 2 ** attempt
                    logger.warning(f"上传超时，{wait_time}秒后重试 ({attempt + 2}/3)...")
                    time.sleep(wait_time)
                    continue
                last_error = Exception("上传超时，请稍后重试")
            except httpx.RequestError as e:
                if attempt < 2:
                    wait_time = 2 ** attempt
                    logger.warning(f"网络错误: {e}，{wait_time}秒后重试 ({attempt + 2}/3)...")
                    time.sleep(wait_time)
                    continue
                last_error = Exception(f"网络连接失败: {e}")

        raise last_error or Exception("文件上传失败")

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        category: str,
        content_type: str = "application/octet-stream",
    ) -> Tuple[str, str]:
        """上传任意文件到 GitHub 的 assets/ 目录

        Returns:
            (cdn_url, file_path)
        """
        if not self.enabled:
            raise Exception("GitHub存储服务未配置：请在 .env 中设置 GITHUB_TOKEN 和 GITHUB_REPO")

        ext = self._get_file_extension(filename)
        category_map = {
            "reference": "images",
            "image": "images",
            "video": "videos",
        }
        storage_category = category_map.get(category, "files")
        file_path = self._generate_path(storage_category, filename or "file.bin")

        cdn_url = await self._upload_to_github(file_path, file_content)
        return cdn_url, file_path

    async def upload_reference_image(
        self, file_content: bytes, filename: str, content_type: str
    ) -> str:
        """上传参考图片"""
        ext = self._get_file_extension(filename)
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise Exception(f"不支持的图片格式: {ext}（支持: png, jpg, jpeg, gif, webp, bmp）")
        if len(file_content) > MAX_IMAGE_SIZE:
            raise Exception("图片大小超过20MB限制")

        cdn_url, _ = await self.upload_file(file_content, filename, "reference", content_type)
        return cdn_url

    async def upload_generated_image(
        self, file_content: bytes, filename: str, content_type: str
    ) -> str:
        """上传生成的图片"""
        if len(file_content) > MAX_IMAGE_SIZE:
            raise Exception("图片大小超过20MB限制")
        cdn_url, _ = await self.upload_file(file_content, filename, "image", content_type)
        return cdn_url

    async def upload_generated_video(
        self, file_content: bytes, filename: str, content_type: str
    ) -> str:
        """上传生成的视频"""
        ext = self._get_file_extension(filename)
        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            raise Exception(f"不支持的视频格式: {ext}（支持: mp4, mov, webm, avi）")
        if len(file_content) > MAX_VIDEO_SIZE:
            raise Exception("视频大小超过100MB限制")
        cdn_url, _ = await self.upload_file(file_content, filename, "video", content_type)
        return cdn_url


_storage_service = None


def get_storage_service() -> GitHubStorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = GitHubStorageService()
    return _storage_service
