from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import time
import json
import hashlib
import base64
import os
import urllib.parse
import io
import mimetypes
import tempfile
import asyncio

import httpx

from app.adapters.base import BaseChannelAdapter
from app.core.logging_config import get_logger
from app.core.config_engine import ConfigEngine
from app.core.cdn import (
    KNOWN_CDN_PREFIXES,
    extract_url_from_image_item,
    is_cdn_url,
    require_cdn_url,
)
from app.core.weelinking_image import normalize_weelinking_gpt_image_body
from app.utils.url_utils import join_url

logger = get_logger()

# 兼容旧引用
_is_cdn_url = is_cdn_url


async def _ensure_cdn_url(url: str, trace_id: str = "") -> str:
    """确保图片URL是CDN地址，如果不是则上传到GitHub获取CDN URL
    
    Args:
        url: 原始图片URL（可能是 data: URL、blob: URL、外部HTTP URL）
        trace_id: 跟踪ID
        
    Returns:
        CDN URL，如果转换失败则返回原始URL
    """
    if not url:
        return url
    
    # 已经是CDN地址，直接返回
    if _is_cdn_url(url):
        return url
    
    # blob: URL 无法处理，记录警告
    if url.startswith("blob:"):
        logger.warning(f"[{trace_id}] 检测到 blob: URL，请先上传图片: {url[:80]}...")
        return url
    
    try:
        from app.services.storage_service import get_storage_service
        storage = get_storage_service()
        
        if not storage.enabled:
            logger.warning(f"[{trace_id}] GitHub存储未启用，无法转换图片URL: {url[:80]}...")
            return url
        
        image_data: bytes = None
        filename = "reference.png"
        content_type = "image/png"
        
        # 处理 data: URL
        if url.startswith("data:"):
            logger.info(f"[{trace_id}] 检测到 data: URL，解码并上传...")
            # 格式: data:image/png;base64,xxxxx
            try:
                header, encoded = url.split(",", 1)
                # 提取 content_type
                if ";" in header:
                    content_type = header.split(":")[1].split(";")[0]
                # 提取扩展名
                ext_map = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif"}
                ext = ext_map.get(content_type, ".png")
                filename = f"ref{ext}"
                image_data = base64.b64decode(encoded)
            except Exception as e:
                logger.error(f"[{trace_id}] data: URL解码失败: {e}")
                return url
        else:
            # HTTP URL - 下载图片
            logger.info(f"[{trace_id}] 下载外部图片: {url[:100]}...")
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        image_data = resp.content
                        content_type = resp.headers.get("content-type", "image/png")
                        # 从URL或content-type推断文件名
                        url_path = urllib.parse.urlparse(url).path
                        if url_path and "." in url_path.split("/")[-1]:
                            filename = url_path.split("/")[-1]
                        else:
                            ext_map = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
                            filename = f"download{ext_map.get(content_type, '.png')}"
                    else:
                        logger.warning(f"[{trace_id}] 下载外部图片失败 HTTP {resp.status_code}: {url[:100]}")
                        return url
            except Exception as e:
                logger.warning(f"[{trace_id}] 下载外部图片异常: {e}, url={url[:100]}")
                return url
        
        if image_data and len(image_data) > 0:
            cdn_url = await storage.upload_reference_image(image_data, filename, content_type)
            logger.info(f"[{trace_id}] 图片已上传到CDN: {url[:60]}... -> {cdn_url}")
            return cdn_url
        else:
            logger.warning(f"[{trace_id}] 未能获取图片数据: {url[:80]}...")
            return url
            
    except Exception as e:
        logger.warning(f"[{trace_id}] 图片CDN转换失败(将使用原始URL): {e}")
        return url


# 图像/视频在渠道侧常为长连接等待；DB 若配 30s 会导致「渠道已成功、平台读超时失败」
_CATEGORY_MIN_READ_TIMEOUT = {
    "image": 300,
    "image_edits": 300,
    "chat": 300,
    "video": 600,
    "video_image": 600,
}


class WeelinkingAdapter(BaseChannelAdapter):
    """Weelink 渠道适配器 - 使用原生 HTTP 请求，精确控制路径与参数

    各分类的请求路径:
    - text: POST <base_url>/chat/completions
    - image: POST <base_url>/images/generations
    - video: POST <base_url>/videos/generations
    """

    def __init__(self, channel_config: Dict[str, Any], trace_id: str):
        super().__init__(channel_config, trace_id)
        self.timeout = self.retry_config.get("timeout", 60)
        self._active_category = "text"
        self.api_config = channel_config.get("api_config", {
            "text_path": "/chat/completions",
            "image_path": "/images/generations",
            "image_edits_path": "/images/edits",  # gpt-image-2 编辑接口
            "video_path": "/videos/generations",
            "text_stream": True,
            "image_api_type": "generations",  # generations 或 edits
        })

    def _http_timeout(self) -> httpx.Timeout:
        """读超时按分类保底，避免生图在渠道完成后平台已断开。"""
        configured = int(self.retry_config.get("timeout", 60) or 60)
        floor = _CATEGORY_MIN_READ_TIMEOUT.get(self._active_category, 60)
        read_seconds = max(configured, floor)
        if read_seconds > configured:
            logger.info(
                f"[{self.trace_id}] 读超时 {configured}s → {read_seconds}s "
                f"(category={self._active_category})"
            )
        return httpx.Timeout(connect=30.0, read=float(read_seconds), write=60.0, pool=30.0)

    @staticmethod
    def _format_request_error(exc: Exception) -> str:
        if isinstance(exc, httpx.TimeoutException):
            return f"{type(exc).__name__}: 等待渠道响应超时（渠道可能仍在生成）"
        msg = str(exc).strip()
        return msg or f"{type(exc).__name__}: 未知网络错误"

    def _raise_http_status_error(self, status_code: int, err_msg: str) -> None:
        """记录上游 HTTP 错误并抛出，供 parse_error / 链路日志展示详情。"""
        body: Any = err_msg
        try:
            body = json.loads(err_msg)
        except Exception:
            pass
        self._last_http_error = {"status_code": status_code, "body": body}
        if status_code == 401:
            raise Exception(f"401 Unauthorized - API Key 无效或过期 (渠道响应: {err_msg})")
        if status_code == 429:
            raise Exception(f"429 Too Many Requests - 超出频率限制或配额不足 (渠道响应: {err_msg})")
        if status_code >= 500:
            raise Exception(f"{status_code} Server Error (渠道响应: {err_msg})")
        raise Exception(f"HTTP {status_code}: {err_msg}")

    async def convert_params(self, model_config: Dict[str, Any], params: Dict[str, Any], endpoint_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 如果有端点配置，检查是否需要应用请求体规范
        if endpoint_config and endpoint_config.get("request_body"):
            try:
                body_schema = json.loads(endpoint_config["request_body"])
                # 可以在这里根据 schema 校验或转换参数
                logger.info(f"[{self.trace_id}] 应用端点请求体规范: {endpoint_config['type']}")
            except Exception as e:
                logger.warning(f"[{self.trace_id}] 解析端点请求体配置失败: {e}")
        return params

    async def _http_post(self, url: str, body: Dict[str, Any], api_key: str,
                         content_type: str = "application/json",
                         extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """统一 HTTP POST 请求，带重试和日志。

        Args:
            content_type: Content-Type，默认 application/json
            extra_headers: 额外 headers（不含 Authorization/Content-Type）
        """
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": content_type,
        }
        if extra_headers:
            for k, v in extra_headers.items():
                if k and k.lower() not in ("authorization", "content-type"):
                    headers[k] = v

        # 记录完整的HTTP请求信息（隐藏API Key）
        safe_headers = {k: v if k.lower() != "authorization" else "Bearer ***" for k, v in headers.items()}
        self._http_request_info = {
            "method": "POST",
            "url": url,
            "headers": safe_headers,
            "body": body,
            "timestamp": time.time()
        }

        await self._flush_outgoing_request_log()

        logger.info(f"[{self.trace_id}] ═════════ POST {url}")
        try:
            safe_body = {k: v for k, v in body.items() if k != "api_key"}
            logger.info(f"[{self.trace_id}] body={json.dumps(safe_body, ensure_ascii=False, indent=2, default=str)[:500]}")
        except Exception:
            pass

        last_error = None
        max_retries = self.retry_config.get("max_retries", 1)

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._http_timeout()) as client:
                    response = await client.post(url, json=body, headers=headers)

                logger.info(f"[{self.trace_id}] HTTP {response.status_code} 响应 (attempt {attempt+1})")

                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.info(f"[{self.trace_id}] 响应数据长度={len(str(data))}")
                        return data
                    except Exception:
                        text = response.text[:300]
                        raise Exception(f"响应非 JSON 格式: {text}")
                else:
                    try:
                        err_json = response.json()
                        err_msg = json.dumps(err_json, ensure_ascii=False, indent=2, default=str)
                    except Exception:
                        err_msg = response.text[:500]
                    logger.error(f"[{self.trace_id}] 渠道错误响应 HTTP {response.status_code}:\n{err_msg}")
                    self._raise_http_status_error(response.status_code, err_msg)
            except Exception as e:
                last_error = e
                logger.warning(
                    f"[{self.trace_id}] HTTP 请求失败 (attempt {attempt+1}): "
                    f"{self._format_request_error(e)}"
                )
                if attempt < max_retries - 1:
                    wait_time = self.retry_config.get("retry_delay", 2)
                    time.sleep(wait_time)

        raise last_error or Exception("HTTP 请求失败")

    async def _download_image_bytes(self, url: str, label: str = "image") -> Tuple[bytes, str]:
        """下载图片，返回 (bytes, content_type)"""
        try:
            timeout = self.timeout
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    raise Exception(f"图片下载失败 HTTP {resp.status_code}: {url[:120]}")
                data = resp.content
                content_type = resp.headers.get("content-type", "image/png")
                if not content_type or not content_type.startswith("image/"):
                    content_type = "image/png"
                logger.info(f"[{self.trace_id}] {label} 下载成功: {len(data)} bytes, content_type={content_type}")
                return data, content_type
        except Exception as e:
            logger.error(f"[{self.trace_id}] {label} 下载失败: {e}")
            raise

    async def _http_post_multipart(
        self,
        url: str,
        fields: Dict[str, Any],
        image_fields: Dict[str, List[bytes]],
        api_key: str,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """使用 multipart/form-data 发送请求（支持多张 images[] 参考图）

        官方接入：同一字段名 images[] 重复多次，每张图一个 part。
        """
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
        }
        if extra_headers:
            for k, v in extra_headers.items():
                if k and k.lower() not in ("authorization", "content-type"):
                    headers[k] = v

        safe_headers = {k: v if k.lower() != "authorization" else "Bearer ***" for k, v in headers.items()}
        safe_fields = {k: v for k, v in fields.items() if k != "api_key"}
        self._http_request_info = {
            "method": "POST",
            "url": url,
            "headers": safe_headers,
            "content_type": "multipart/form-data",
            "text_fields": safe_fields,
            "image_fields": {k: [len(b) for b in v] for k, v in image_fields.items()},
            "timestamp": time.time(),
        }

        await self._flush_outgoing_request_log()

        logger.info(f"[{self.trace_id}] ═════════ MULTIPART POST {url}")
        try:
            logger.info(
                f"[{self.trace_id}] text_fields={json.dumps(safe_fields, ensure_ascii=False, indent=2, default=str)[:800]}"
            )
            logger.info(
                f"[{self.trace_id}] image_fields={[(k, [len(b) for b in v]) for k, v in image_fields.items()]}"
            )
        except Exception:
            pass

        def _guess_image_meta(img_bytes: bytes, idx: int) -> Tuple[str, str, str]:
            ext = ".png"
            header = img_bytes[:4] if len(img_bytes) >= 4 else b""
            if header.startswith(b"\xff\xd8\xff"):
                ext = ".jpg"
            elif header.startswith(b"\x89PNG"):
                ext = ".png"
            elif header.startswith(b"RIFF"):
                ext = ".webp"
            elif header.startswith(b"GIF8"):
                ext = ".gif"
            filename = f"image_{idx + 1}{ext}"
            content_type = f"image/{ext[1:]}"
            return filename, content_type, ext

        last_error = None
        max_retries = self.retry_config.get("max_retries", 1)

        for attempt in range(max_retries):
            try:
                data_payload: Dict[str, Any] = {}
                for k, v in fields.items():
                    if v is None:
                        continue
                    if isinstance(v, (list, dict)):
                        data_payload[k] = json.dumps(v, ensure_ascii=False)
                    else:
                        data_payload[k] = str(v)

                # httpx 多文件同名字段须用 list of tuples，不能用 dict（会覆盖）
                files_list: List[Tuple[str, Tuple[str, bytes, str]]] = []
                file_idx = 0
                for field_name, images_list in image_fields.items():
                    for img_bytes in images_list:
                        if not img_bytes:
                            continue
                        filename, content_type, _ = _guess_image_meta(img_bytes, file_idx)
                        files_list.append((field_name, (filename, img_bytes, content_type)))
                        file_idx += 1

                async with httpx.AsyncClient(timeout=self._http_timeout()) as client:
                    response = await client.post(
                        url,
                        headers=headers,
                        data=data_payload if data_payload else None,
                        files=files_list if files_list else None,
                    )

                logger.info(f"[{self.trace_id}] HTTP {response.status_code} 响应 (attempt {attempt+1})")

                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.info(f"[{self.trace_id}] 响应数据长度={len(str(data))}")
                        return data
                    except Exception:
                        text = response.text[:300]
                        raise Exception(f"响应非 JSON 格式: {text}")
                else:
                    try:
                        err_json = response.json()
                        err_msg = json.dumps(err_json, ensure_ascii=False, indent=2)
                    except Exception:
                        err_msg = response.text[:500]
                    logger.error(f"[{self.trace_id}] 渠道错误响应 HTTP {response.status_code}:\n{err_msg}")
                    self._raise_http_status_error(response.status_code, err_msg)
            except Exception as e:
                last_error = e
                logger.warning(
                    f"[{self.trace_id}] HTTP 请求失败 (attempt {attempt+1}): "
                    f"{self._format_request_error(e)}"
                )
                if attempt < max_retries - 1:
                    wait_time = self.retry_config.get("retry_delay", 2)
                    time.sleep(wait_time)

        raise last_error or Exception("HTTP 请求失败")

    async def _http_post_stream(self, url: str, body: Dict[str, Any], api_key: str,
                                 content_type: str = "application/json",
                                 extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """流式 HTTP POST 请求，处理 stream=True 的响应"""
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": content_type,
        }
        if extra_headers:
            for k, v in extra_headers.items():
                if k and k.lower() not in ("authorization", "content-type"):
                    headers[k] = v

        # 记录完整的HTTP请求信息（隐藏API Key）
        safe_headers = {k: v if k.lower() != "authorization" else "Bearer ***" for k, v in headers.items()}
        self._http_request_info = {
            "method": "POST",
            "url": url,
            "headers": safe_headers,
            "body": body,
            "timestamp": time.time(),
            "stream": True
        }

        logger.info(f"[{self.trace_id}] ═════════ POST STREAM {url}")
        try:
            safe_body = {k: v for k, v in body.items() if k != "api_key"}
            logger.info(f"[{self.trace_id}] body={json.dumps(safe_body, ensure_ascii=False, indent=2)[:500]}")
        except Exception:
            pass

        last_error = None
        max_retries = self.retry_config.get("max_retries", 1)

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._http_timeout()) as client:
                    async with client.stream("POST", url, json=body, headers=headers) as response:
                        logger.info(f"[{self.trace_id}] HTTP {response.status_code} 流式响应 (attempt {attempt+1})")

                        if response.status_code == 200:
                            full_content = ""
                            async for line in response.aiter_lines():
                                if line.startswith("data: "):
                                    data_str = line[6:]
                                    if data_str.strip() == "[DONE]":
                                        break
                                    try:
                                        data = json.loads(data_str)
                                        choices = data.get("choices", [])
                                        if choices:
                                            delta = choices[0].get("delta", {})
                                            content = delta.get("content", "")
                                            if content:
                                                full_content += content
                                    except json.JSONDecodeError:
                                        pass
                            
                            # 构建模拟非流式响应格式供 parse_result 处理
                            return {
                                "choices": [{
                                    "message": {"content": full_content},
                                    "finish_reason": "stop"
                                }],
                                "usage": {}
                            }
                        else:
                            try:
                                err_json = await response.json()
                                err_msg = json.dumps(err_json, ensure_ascii=False, indent=2)
                            except Exception:
                                err_msg = (await response.aread()).decode('utf-8')[:500]
                            logger.error(f"[{self.trace_id}] 渠道错误响应 HTTP {response.status_code}:\n{err_msg}")
                            self._raise_http_status_error(response.status_code, err_msg)
            except Exception as e:
                last_error = e
                logger.warning(
                    f"[{self.trace_id}] 流式请求失败 (attempt {attempt+1}): "
                    f"{self._format_request_error(e)}"
                )
                if attempt < max_retries - 1:
                    wait_time = self.retry_config.get("retry_delay", 2)
                    time.sleep(wait_time)

        raise last_error or Exception("流式 HTTP 请求失败")

    async def call_api(self, category: str, channel_params: Dict[str, Any], channel_model_id: str, api_key: str, endpoint_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._active_category = (
            endpoint_config.get("type") if endpoint_config else None
        ) or category
        logger.info(f"[{self.trace_id}] call_api - category={category}, base_url={self.base_url}, model={channel_model_id}")

        if not api_key:
            raise Exception(f"渠道 API Key 未配置: category={category}, channel={self.channel_code}")

        # 如果有端点配置，使用动态端点调用
        if endpoint_config:
            return await self._call_dynamic_api(category, channel_params, channel_model_id, api_key, endpoint_config)

        # 回退到旧的分类路由方式（兼容旧配置）
        if category == "text":
            return await self._call_text_api(channel_params, channel_model_id, api_key)
        elif category == "image":
            return await self._call_image_api(channel_params, channel_model_id, api_key)
        elif category == "video":
            return await self._call_video_api(channel_params, channel_model_id, api_key)
        else:
            raise Exception(f"不支持的分类: {category}")

    async def _call_dynamic_api(self, category: str, channel_params: Dict[str, Any], channel_model_id: str, api_key: str, endpoint_config: Dict[str, Any]) -> Dict[str, Any]:
        """根据端点配置动态调用API - 配置化引擎驱动"""
        endpoint_type = endpoint_config.get("type", category)
        endpoint_path = endpoint_config.get("endpoint", "")
        method = endpoint_config.get("method", "POST").upper()

        # 从端点配置读取 content_type / headers（新配置优先）
        content_type = "application/json"
        extra_headers: Dict[str, str] = {}
        body_type_config = (
            endpoint_config.get("content_type")
            or endpoint_config.get("content-type")
            or endpoint_config.get("body_type", "")
        ).lower()
        if body_type_config.startswith("multipart"):
            pass
        elif body_type_config and body_type_config != "json":
            content_type = body_type_config
        headers_config = endpoint_config.get("headers")
        if isinstance(headers_config, dict):
            extra_headers = {str(k): str(v) for k, v in headers_config.items()}

        if not endpoint_path:
            # 没有配置端点路径，回退到默认处理
            logger.warning(f"[{self.trace_id}] 端点配置缺少 endpoint，回退到默认处理")
            if category == "text":
                return await self._call_text_api(channel_params, channel_model_id, api_key)
            elif category == "image":
                return await self._call_image_api(channel_params, channel_model_id, api_key)
            elif category == "video":
                return await self._call_video_api(channel_params, channel_model_id, api_key)
            else:
                raise Exception(f"不支持的分类: {category}")

        url = join_url(self.base_url, endpoint_path)

        # 检查是否有配置化参数模板（新的 body_params 优先）
        has_template = (
            endpoint_config.get("body_params")
            or endpoint_config.get("params_template")
            or endpoint_config.get("param_mappings")
        )

        # 解析 body_type: multipart / json（默认）
        body_type = body_type_config or endpoint_config.get("body_type", "").lower()
        image_param_names = endpoint_config.get("image_param_names", ["image", "images", "images[]"])

        if has_template:
            # 使用配置化引擎构建请求体
            logger.info(f"[{self.trace_id}] 使用配置化引擎构建请求 - type={endpoint_type}, body_type={body_type}")
            body = ConfigEngine.build_request_body(
                endpoint_config=endpoint_config,
                params=channel_params,
                model_id=channel_model_id,
                channel_code=self.channel_code,
                trace_id=self.trace_id,
            )
        else:
            # 无模板，回退到原有的硬编码逻辑（兼容旧配置）
            logger.info(f"[{self.trace_id}] 动态端点调用 - type={endpoint_type}, path={endpoint_path}, method={method}")
            body = await self._build_request_body(endpoint_type, channel_params, channel_model_id)

        # text/chat 端点：body_params 未显式配置 stream 时，回退到 api_config.text_stream
        if endpoint_type in ("text", "chat"):
            if "stream" in channel_params:
                body["stream"] = bool(channel_params["stream"])
            elif "stream" not in body:
                body["stream"] = self.api_config.get("text_stream", True)
                logger.info(
                    f"[{self.trace_id}] body_params 未配置 stream，"
                    f"从 api_config.text_stream 注入: {body['stream']}"
                )

        logger.info(f"[{self.trace_id}] URL={url}, method={method}, content_type={content_type}")

        # multipart/form-data 分支：下载图片文件，作为表单文件上传
        if body_type.startswith("multipart"):
            if endpoint_type in ("image", "image_edits"):
                edit_params = {**channel_params, "trace_id": self.trace_id}
                body = normalize_weelinking_gpt_image_body(
                    body, edit_params, endpoint="image_edits" if endpoint_type == "image_edits" else "generations"
                )
                if endpoint_type != "image_edits":
                    body.setdefault("n", channel_params.get("n", channel_params.get("count", 1)))

            # 分离文本字段和图片字段
            text_fields: Dict[str, Any] = {}
            image_bytes_map: Dict[str, List[bytes]] = {}

            for k, v in body.items():
                # 图片字段：包含图片URL数组或单URL
                is_image_field = any(
                    name.lower() in k.lower() for name in image_param_names
                ) or (
                    isinstance(v, str) and v.startswith("http") and is_cdn_url(v)
                )

                if is_image_field and isinstance(v, (list, str)):
                    urls = v if isinstance(v, list) else [v]
                    bytes_list: List[bytes] = []
                    for idx, u in enumerate(urls[:16]):
                        try:
                            img_url = u if isinstance(u, str) else extract_url_from_image_item(u)
                            if not img_url:
                                continue
                            img_bytes, _ = await self._download_image_bytes(
                                img_url, label=f"image[{idx}]"
                            )
                            bytes_list.append(img_bytes)
                        except Exception as e:
                            logger.warning(f"[{self.trace_id}] 跳过图片字段 {k}[{idx}]: {e}")
                    if bytes_list:
                        field_name = k if k.endswith("[]") or "[]" in k else "images[]"
                        image_bytes_map[field_name] = image_bytes_map.get(field_name, []) + bytes_list
                else:
                    text_fields[k] = v

            if not image_bytes_map:
                raise Exception("图生图需要至少一张参考图（images[]），请上传 CDN 图片后重试")

            logger.info(
                f"[{self.trace_id}] multipart 请求 - text_keys={list(text_fields.keys())}, "
                f"image_counts={[(k, len(v)) for k, v in image_bytes_map.items()]}"
            )
            response = await self._http_post_multipart(
                url, text_fields, image_bytes_map, api_key,
                extra_headers=extra_headers,
            )
            return {"type": endpoint_type, "response": response}

        # 根据方法调用（JSON body）
        if method == "POST":
            if endpoint_type in ("image", "image_edits"):
                body = normalize_weelinking_gpt_image_body(
                    body,
                    channel_params,
                    endpoint="image_edits" if endpoint_type == "image_edits" else "generations",
                )
            # 根据 body 中的 stream 字段决定走流式还是非流式请求
            use_stream = bool(body.get("stream", False))
            if use_stream:
                logger.info(f"[{self.trace_id}] 使用流式请求 (stream=True)")
                response = await self._http_post_stream(
                    url, body, api_key, content_type, extra_headers
                )
            else:
                response = await self._http_post(url, body, api_key, content_type, extra_headers)
        elif method == "GET":
            query_url = url + "?" + urllib.parse.urlencode(body)
            response = await self._http_get(query_url, api_key, extra_headers=extra_headers)
        else:
            raise Exception(f"不支持的HTTP方法: {method}")

        return {"type": endpoint_type, "response": response}

    async def _http_get(self, url: str, api_key: str,
                         extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """HTTP GET 请求"""
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
        }
        if extra_headers:
            headers.update(extra_headers)

        logger.info(f"[{self.trace_id}] ═════════ GET {url}")

        async with httpx.AsyncClient(timeout=self._http_timeout()) as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text[:500]}")

    async def _build_request_body(self, endpoint_type: str, channel_params: Dict[str, Any], channel_model_id: str) -> Dict[str, Any]:
        """根据端点类型构建请求体"""
        body: Dict[str, Any] = {
            "model": channel_model_id,
            "prompt": channel_params.get("prompt", ""),
        }

        if endpoint_type in ("image", "image_edits"):
            # 图片相关端点
            body["n"] = channel_params.get("n", channel_params.get("count", 1))
            body["size"] = channel_params.get("size", "auto")
            
            if "negative_prompt" in channel_params:
                body["negative_prompt"] = str(channel_params["negative_prompt"])
            if "input_fidelity" in channel_params:
                body["input_fidelity"] = float(channel_params["input_fidelity"])
            if "aspect_ratio" in channel_params:
                body["aspect_ratio"] = str(channel_params["aspect_ratio"])
            if "seed" in channel_params:
                body["seed"] = int(channel_params["seed"])
            if "quality" in channel_params:
                body["quality"] = str(channel_params["quality"])
            
            # 参考图处理
            raw_items: List[Any] = []
            if "image" in channel_params:
                img_val = channel_params["image"]
                if isinstance(img_val, list):
                    raw_items.extend(img_val)
                elif isinstance(img_val, str):
                    raw_items.append(img_val)
            if not raw_items and "images" in channel_params and isinstance(channel_params["images"], list):
                raw_items.extend(channel_params["images"])
            
            if raw_items:
                image_urls: List[str] = []
                for i, item in enumerate(raw_items[:16]):
                    img_url = extract_url_from_image_item(item)
                    cdn_url = require_cdn_url(img_url, label=f"参考图[{i + 1}]")
                    image_urls.append(cdn_url)
                body["image"] = image_urls

        elif endpoint_type in ("video", "video_image"):
            # 视频相关端点
            body["n"] = channel_params.get("n", 1)
            if "size" in channel_params:
                body["size"] = str(channel_params["size"])
            if "duration" in channel_params:
                body["duration"] = str(channel_params["duration"])
            if "negative_prompt" in channel_params:
                body["negative_prompt"] = str(channel_params["negative_prompt"])
            if "seed" in channel_params:
                body["seed"] = int(channel_params["seed"])
            if "reference_image" in channel_params:
                body["reference_image"] = channel_params["reference_image"]

        elif endpoint_type in ("text", "chat"):
            # 文本端点和对话式端点
            # 构建消息内容（支持多模态：文本 + 图片）
            prompt = body["prompt"]
            images = channel_params.get("images", [])
            
            content: List[Dict[str, Any]] = []
            if prompt:
                content.append({"type": "text", "text": prompt})
            
            # 添加图片（支持多张），必须为 CDN 地址
            for img in images:
                img_url = extract_url_from_image_item(img) if not isinstance(img, str) else img
                if isinstance(img_url, str) and img_url:
                    cdn_url = require_cdn_url(img_url, label="参考图")
                    content.append({"type": "image_url", "image_url": {"url": cdn_url}})
            
            # 检查是否有单独的 image 参数（图生图场景）
            if not images and channel_params.get("image"):
                img_val = channel_params["image"]
                if isinstance(img_val, list):
                    for img in img_val:
                        img_url = extract_url_from_image_item(img) if not isinstance(img, str) else img
                        if isinstance(img_url, str) and img_url:
                            cdn_url = require_cdn_url(img_url, label="参考图")
                            content.append({"type": "image_url", "image_url": {"url": cdn_url}})
                elif isinstance(img_val, str):
                    cdn_url = require_cdn_url(img_val, label="参考图")
                    content.append({"type": "image_url", "image_url": {"url": cdn_url}})
            
            # 获取现有消息或创建新消息
            existing_messages = channel_params.get("messages", [])
            if existing_messages:
                # 如果已有消息，更新最后一条消息的内容
                messages = existing_messages.copy()
                last_msg = messages[-1].copy()
                last_msg["content"] = content if content else prompt
                messages[-1] = last_msg
            else:
                messages = [{"role": "user", "content": content if content else prompt}]
            
            body["messages"] = messages
            body["stream"] = self.api_config.get("text_stream", True)
            
            if "temperature" in channel_params:
                body["temperature"] = float(channel_params["temperature"])
            if "max_tokens" in channel_params:
                body["max_tokens"] = int(channel_params["max_tokens"])
            if "seed" in channel_params:
                body["seed"] = int(channel_params["seed"])
            
            if endpoint_type == "chat":
                # 对话式端点额外参数
                if "top_p" in channel_params:
                    body["top_p"] = float(channel_params["top_p"])
                if "frequency_penalty" in channel_params:
                    body["frequency_penalty"] = float(channel_params["frequency_penalty"])
                if "presence_penalty" in channel_params:
                    body["presence_penalty"] = float(channel_params["presence_penalty"])
            
            # 图片相关参数（对话式端点支持文生图和图生图）
            if channel_params.get("image") or channel_params.get("images"):
                # 有图片时添加图片生成相关参数
                if "n" in channel_params:
                    body["n"] = int(channel_params["n"])
                if "size" in channel_params:
                    body["size"] = str(channel_params["size"])
                if "aspect_ratio" in channel_params:
                    body["aspect_ratio"] = str(channel_params["aspect_ratio"])
                if "negative_prompt" in channel_params:
                    body["negative_prompt"] = str(channel_params["negative_prompt"])
                if "quality" in channel_params:
                    body["quality"] = str(channel_params["quality"])

        else:
            # 其他端点类型，直接传递参数
            body.update(channel_params)

        return body

    async def _call_text_api(self, channel_params: Dict[str, Any], channel_model_id: str, api_key: str) -> Dict[str, Any]:
        """文本生成：POST /chat/completions
        
        支持图片输入（vision）和流式响应配置
        """
        text_path = self.api_config.get("text_path", "/chat/completions")
        url = join_url(self.base_url, text_path)
        prompt = channel_params.get("prompt", "")
        messages = channel_params.get("messages")
        images = channel_params.get("images", [])

        if not messages:
            content: List[Dict[str, Any]] = []
            
            # 添加文本提示
            if prompt:
                content.append({"type": "text", "text": prompt})
            
            # 添加图片（支持多张），必须为 CDN 地址
            for img in images:
                img_url = extract_url_from_image_item(img) if not isinstance(img, str) else img
                if isinstance(img_url, str) and img_url:
                    cdn_url = require_cdn_url(img_url, label="参考图")
                    content.append({"type": "image_url", "image_url": {"url": cdn_url}})
            
            messages = [
                {"role": "user", "content": content if content else prompt if prompt else "你好"},
            ]
        elif messages and not messages[-1].get("content"):
            content: List[Dict[str, Any]] = []
            if prompt:
                content.append({"type": "text", "text": prompt})
            for img in images:
                # 支持字符串格式和对象格式 {"cdn_url"/"url": "...", "file_name": "..."}
                img_url = extract_url_from_image_item(img) if not isinstance(img, str) else img
                if isinstance(img_url, str) and img_url:
                    cdn_url = require_cdn_url(img_url, label="参考图")
                    content.append({"type": "image_url", "image_url": {"url": cdn_url}})
            
            messages = [
                {"role": "user", "content": content if content else prompt if prompt else "你好"},
            ]

        body: Dict[str, Any] = {
            "model": channel_model_id,
            "messages": messages,
        }
        
        # 根据配置决定是否使用流式响应
        use_stream = self.api_config.get("text_stream", True)
        body["stream"] = use_stream
        
        if "temperature" in channel_params:
            body["temperature"] = float(channel_params["temperature"])
        if "max_tokens" in channel_params:
            body["max_tokens"] = int(channel_params["max_tokens"])
        if "seed" in channel_params:
            body["seed"] = int(channel_params["seed"])

        logger.info(f"[{self.trace_id}] text_stream={use_stream}, images={len(images)}")
        
        if use_stream:
            response = await self._http_post_stream(url, body, api_key)
        else:
            response = await self._http_post(url, body, api_key)
            
        return {"type": "text", "response": response}

    async def _call_image_api(self, channel_params: Dict[str, Any], channel_model_id: str, api_key: str) -> Dict[str, Any]:
        """图片生成：POST /images/generations 或 /images/edits

        策略：
        - 使用 /images/edits + multipart/form-data 发送图片文件
        - 或使用 /images/generations + JSON body 发送图片 URL
        """
        # 判断是否有参考图
        has_reference_image = False
        raw_items: List[Any] = []
        if "image" in channel_params:
            img_val = channel_params["image"]
            if isinstance(img_val, list):
                raw_items.extend(img_val)
            elif isinstance(img_val, str):
                raw_items.append(img_val)
        if not raw_items and "images" in channel_params and isinstance(channel_params["images"], list):
            raw_items.extend(channel_params["images"])

        has_reference_image = len(raw_items) > 0

        # 根据配置选择端点：有参考图且配置允许，使用 edits 端点
        image_api_type = self.api_config.get("image_api_type", "generations")

        if has_reference_image and image_api_type == "edits":
            image_path = self.api_config.get("image_edits_path", "/images/edits")
        else:
            image_path = self.api_config.get("image_path", "/images/generations")

        url = join_url(self.base_url, image_path)
        prompt = channel_params.get("prompt", "")

        logger.info(
            f"[{self.trace_id}] 图片生成 - endpoint={image_path}, "
            f"has_reference={has_reference_image}, model={channel_model_id}"
        )

        body: Dict[str, Any] = {
            "model": channel_model_id,
            "prompt": prompt,
            "n": 1,
            "size": "auto",
        }

        if "negative_prompt" in channel_params:
            body["negative_prompt"] = str(channel_params["negative_prompt"])

        if "n" in channel_params:
            body["n"] = max(1, min(10, int(channel_params["n"])))
        elif "count" in channel_params:
            body["n"] = max(1, min(10, int(channel_params["count"])))

        if "aspect_ratio" in channel_params and not (
            channel_params.get("size")
            and str(channel_params["size"]).strip().lower() not in ("", "auto")
            and "x" in str(channel_params["size"])
        ):
            body["aspect_ratio"] = str(channel_params["aspect_ratio"])
            body["size"] = "auto"
        elif "size" in channel_params:
            size_val = channel_params["size"]
            if isinstance(size_val, dict) and size_val.get("width") and size_val.get("height"):
                body["width"] = int(size_val["width"])
                body["height"] = int(size_val["height"])
            else:
                body["size"] = str(size_val)
        elif "width" in channel_params and "height" in channel_params:
            body["width"] = int(channel_params["width"])
            body["height"] = int(channel_params["height"])

        if "input_fidelity" in channel_params:
            body["input_fidelity"] = max(0.0, min(1.0, float(channel_params["input_fidelity"])))
        elif has_reference_image:
            body["input_fidelity"] = 0.7

        if "quality" in channel_params:
            body["quality"] = str(channel_params["quality"])

        if "output_format" in channel_params:
            body["output_format"] = str(channel_params["output_format"])

        if "response_format" in channel_params:
            body["response_format"] = str(channel_params["response_format"])

        if "thinking" in channel_params:
            body["thinking"] = str(channel_params["thinking"])

        if "stream" in channel_params:
            body["stream"] = bool(channel_params["stream"])

        if "user" in channel_params:
            body["user"] = str(channel_params["user"])

        if "seed" in channel_params:
            body["seed"] = int(channel_params["seed"])

        edit_params = {**channel_params, "trace_id": self.trace_id}
        body = normalize_weelinking_gpt_image_body(
            body,
            edit_params,
            endpoint="image_edits" if has_reference_image else "generations",
        )

        # 关键逻辑：使用 image_edits 端点时走 multipart/form-data，images[] 字段作为文件上传
        use_multipart = has_reference_image and (
            "edits" in image_path
            or "image_edits" in image_path
            or channel_params.get("_use_multipart")
            or self.api_config.get("use_multipart", False)
        )

        if use_multipart:
            # 收集参考图（从 URL 下载 bytes）
            image_bytes_list: List[bytes] = []
            for i, item in enumerate(raw_items[:16]):
                img_url = extract_url_from_image_item(item)
                if not img_url:
                    continue
                try:
                    img_bytes, _ = await self._download_image_bytes(
                        img_url, label=f"参考图[{i + 1}]"
                    )
                    image_bytes_list.append(img_bytes)
                except Exception as e:
                    logger.warning(f"[{self.trace_id}] 参考图下载失败，跳过: {e}")

            # 如果成功下载了图片，则走 multipart
            if image_bytes_list:
                image_fields = {"images[]": image_bytes_list}
                # 对 multipart 场景，避免 JSON 字段冲突，挑出必要字段
                multipart_fields: Dict[str, Any] = {
                    "model": body.get("model", channel_model_id),
                    "prompt": prompt,
                }
                for k in ("size", "width", "height", "aspect_ratio",
                          "quality", "output_format", "response_format", "background",
                          "output_compression", "user",
                          "thinking", "seed", "input_fidelity", "negative_prompt"):
                    if k in body:
                        multipart_fields[k] = body[k]

                logger.info(
                    f"[{self.trace_id}] 使用 multipart/form-data 发送 "
                    f"image_edits 请求，images[]={len(image_bytes_list)} 张"
                )
                response = await self._http_post_multipart(
                    url, multipart_fields, image_fields, api_key
                )
                return {"type": "image", "response": response}

            # 如果没有可用图片，则回落为 JSON 调用
            logger.warning(
                f"[{self.trace_id}] multipart 图片为空，回落为 JSON 调用"
            )

        # JSON body：image 字段使用 CDN URL 数组
        if raw_items and not use_multipart:
            image_urls: List[str] = []
            for i, item in enumerate(raw_items[:16]):
                img_url = extract_url_from_image_item(item)
                cdn_url = require_cdn_url(img_url, label=f"参考图[{i + 1}]")
                image_urls.append(cdn_url)
                logger.info(f"[{self.trace_id}] 参考图[{i}]: {cdn_url[:80]}...")
            body["image"] = image_urls

        response = await self._http_post(url, body, api_key)
        return {"type": "image", "response": response}


    async def _call_video_api(self, channel_params: Dict[str, Any], channel_model_id: str, api_key: str) -> Dict[str, Any]:
        """视频生成：POST /videos/generations"""
        video_path = self.api_config.get("video_path", "/videos/generations")
        url = join_url(self.base_url, video_path)
        prompt = channel_params.get("prompt", "")

        body: Dict[str, Any] = {
            "model": channel_model_id,
            "prompt": prompt,
            "n": 1,
        }
        if "size" in channel_params:
            body["size"] = str(channel_params["size"])
        if "duration" in channel_params:
            body["duration"] = str(channel_params["duration"])
        if "first_frame_image" in channel_params:
            body["first_frame_image"] = channel_params["first_frame_image"]
        if "last_frame_image" in channel_params:
            body["last_frame_image"] = channel_params["last_frame_image"]
        if "reference_image" in channel_params:
            body["reference_image"] = channel_params["reference_image"]
        if "negative_prompt" in channel_params:
            body["negative_prompt"] = str(channel_params["negative_prompt"])
        if "seed" in channel_params:
            body["seed"] = int(channel_params["seed"])
        if "motion_scale" in channel_params:
            body["motion_scale"] = int(channel_params["motion_scale"])

        response = await self._http_post(url, body, api_key)
        return {"type": "video", "response": response}

    async def _upload_base64_image(self, base64_data: str) -> Optional[str]:
        """将base64图片上传到GitHub存储，返回CDN URL"""
        return await self._upload_base64_blob(base64_data, ".png", "image/png")

    async def _upload_base64_blob(
        self, base64_data: str, ext: str = ".png", content_type: str = "image/png"
    ) -> Optional[str]:
        """将 base64 二进制上传到存储，返回 CDN URL"""
        try:
            import base64
            from app.services.storage_service import get_storage_service
            from datetime import datetime

            raw = base64_data.strip()
            if raw.startswith("data:"):
                raw = raw.split(",", 1)[1]
            blob = base64.b64decode(raw)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}{ext}"

            storage = get_storage_service()
            if not storage.enabled:
                logger.warning(f"[{self.trace_id}] 存储服务未启用，无法上传 base64 媒体")
                return None

            if content_type.startswith("video/"):
                url = await storage.upload_generated_video(blob, filename, content_type)
            else:
                url = await storage.upload_generated_image(blob, filename, content_type)
            if url:
                logger.info(f"[{self.trace_id}] base64 媒体上传成功: {url[:80]}")
                return url
            logger.warning(f"[{self.trace_id}] base64 媒体上传失败")
            return None
        except Exception as e:
            logger.error(f"[{self.trace_id}] 上传 base64 媒体异常: {e}")
            return None

    async def normalize_parsed_result(
        self,
        parsed: Dict[str, Any],
        raw_result: Dict[str, Any],
        category: str,
        endpoint_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        from app.core.channel_media import enrich_parsed_result

        async def upload_b64(data: str, ext: str) -> Optional[str]:
            ctype = "video/mp4" if ext == ".mp4" else "image/png"
            return await self._upload_base64_blob(data, ext, ctype)

        return await enrich_parsed_result(
            parsed,
            raw_result.get("response", raw_result),
            category,
            upload_b64=upload_b64,
            trace_id=self.trace_id,
        )

    async def parse_result(self, category: str, raw_result: Dict[str, Any], endpoint_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        result_type = raw_result.get("type", category)
        
        # 文本类端点（text, chat）
        if result_type in ("text", "chat"):
            response = raw_result["response"]
            
            # 检查是否是图片响应（对话式端点可能返回图片）
            if response.get("data"):
                # 图片响应格式
                image_data = response.get("data", [])
                images = []
                for item in image_data:
                    img_url = item.get("url")
                    if not img_url and item.get("b64_json"):
                        uploaded_url = await self._upload_base64_image(item["b64_json"])
                        if uploaded_url:
                            img_url = uploaded_url
                        else:
                            img_url = f"data:image/png;base64,{item['b64_json']}"
                    images.append({
                        "url": img_url,
                        "revised_prompt": item.get("revised_prompt", ""),
                    })
                return {
                    "type": "image",
                    "images": images,
                    "count": len(images),
                }
            
            # 文本响应格式
            choices = response.get("choices", [])
            text_content = ""
            if choices:
                msg = choices[0].get("message", {})
                text_content = msg.get("content", "")
                if not text_content and choices[0].get("delta"):
                    text_content = choices[0]["delta"].get("content", "")
            return {
                "type": "text",
                "text": text_content,
                "choices": choices,
                "usage": response.get("usage"),
            }

        # 图片类端点（image, image_edits）
        elif result_type in ("image", "image_edits"):
            response = raw_result["response"]
            image_data = response.get("data", [])
            images = []
            for item in image_data:
                img_url = item.get("url")
                if not img_url and item.get("b64_json"):
                    uploaded_url = await self._upload_base64_image(item["b64_json"])
                    if uploaded_url:
                        img_url = uploaded_url
                    else:
                        img_url = f"data:image/png;base64,{item['b64_json']}"
                images.append({
                    "url": img_url,
                    "revised_prompt": item.get("revised_prompt", ""),
                })
            return {
                "type": "image",
                "images": images,
                "count": len(images),
            }

        # 视频类端点（video, video_image）
        elif result_type in ("video", "video_image"):
            response = raw_result["response"]
            video_data = response.get("data", []) if isinstance(response, dict) else []
            # 兼容可能的其他响应结构
            if not video_data and isinstance(response, dict):
                for key in ("videos", "items", "results"):
                    if key in response:
                        video_data = response[key]
                        break
            videos = []
            for item in video_data:
                if isinstance(item, str):
                    videos.append({"url": item, "revised_prompt": ""})
                elif isinstance(item, dict):
                    url = item.get("url") or item.get("video_url")
                    if not url and item.get("b64_json"):
                        uploaded = await self._upload_base64_blob(
                            item["b64_json"], ".mp4", "video/mp4"
                        )
                        url = uploaded or f"data:video/mp4;base64,{item['b64_json']}"
                    if url:
                        videos.append({
                            "url": url,
                            "revised_prompt": item.get("revised_prompt", ""),
                        })
            return {
                "type": "video",
                "videos": videos,
                "count": len(videos),
            }

        # 音频类端点（audio）
        elif result_type == "audio":
            response = raw_result["response"]
            audio_data = response.get("data", []) if isinstance(response, dict) else []
            audios = []
            for item in audio_data:
                if isinstance(item, str):
                    audios.append({"url": item})
                elif isinstance(item, dict):
                    audios.append({
                        "url": item.get("url"),
                        "duration": item.get("duration"),
                    })
            return {
                "type": "audio",
                "audios": audios,
                "count": len(audios),
            }

        # 其他未知类型
        else:
            return {"type": result_type, "raw": raw_result}

    def parse_error(self, exception: Exception) -> tuple[str, str]:
        if isinstance(exception, httpx.TimeoutException):
            return "timeout", "生成超时：渠道可能仍在处理，请稍后重试或增大渠道超时配置"

        err_msg = str(exception)
        err_lower = err_msg.lower()
        upstream = ""
        if "渠道响应:" in err_msg:
            upstream = err_msg.split("渠道响应:", 1)[1].strip()
            if len(upstream) > 400:
                upstream = upstream[:400] + "…"

        def with_upstream(base: str) -> str:
            return f"{base}（上游: {upstream}）" if upstream else base

        if "401" in err_lower or "unauthorized" in err_lower or "invalid" in err_lower and "key" in err_lower:
            return "channel_error", with_upstream("渠道鉴权失败，请检查API密钥")
        elif "429" in err_lower or "rate" in err_lower or "quota" in err_lower or "frequency" in err_lower:
            return "service_unavailable", with_upstream("模型服务繁忙，请稍后再试")
        elif "timeout" in err_lower or "timed out" in err_lower:
            return "timeout", with_upstream("生成超时，请稍后重试")
        elif "content_policy" in err_lower or "safety" in err_lower or "violation" in err_lower:
            return "content_violation", with_upstream("内容不符合规范，请调整提示词")
        elif "not_found" in err_lower or "404" in err_lower or "not found" in err_lower:
            return "channel_error", with_upstream("模型不存在或已下线")
        elif "500" in err_lower or "502" in err_lower or "503" in err_lower or "server error" in err_lower:
            return "service_unavailable", with_upstream("服务暂不可用")
        else:
            return "internal_error", f"生成失败: {err_msg[:200]}"
