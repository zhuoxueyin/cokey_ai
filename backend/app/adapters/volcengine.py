from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
import time
import json
import asyncio

import httpx

from app.adapters.base import BaseChannelAdapter
from app.core.cdn import extract_url_from_image_item, require_cdn_url
from app.core.config_engine import ConfigEngine
from app.core.logging_config import get_logger
from app.core.volcengine_video import is_volcengine_video_endpoint
from app.utils.url_utils import join_url

logger = get_logger()


class VolcengineAdapter(BaseChannelAdapter):
    """火山引擎渠道适配器

    API 格式参考:
    文本对话（兼容 OpenAI 格式）:
      POST {base_url}/api/v3/responses  或  /api/v3/chat/completions

    视频生成（异步）:
      POST {base_url}/api/v3/contents/generations/tasks   (创建任务)
      GET  {base_url}/api/v3/contents/generations/tasks/{id}   (查询状态)

    Authorization: Bearer <api_key>
    Content-Type: application/json

    动态端点（通过 endpoints 配置）：
      - 类型为 text/chat/image/video 的端点会走 _call_dynamic_api
      - 未配置 endpoints 时，回落到默认路径（视频有完整轮询逻辑）
    """

    def __init__(self, channel_config: Dict[str, Any], trace_id: str):
        super().__init__(channel_config, trace_id)
        self.timeout = self.retry_config.get("timeout", 120)
        self.poll_interval = self.retry_config.get("poll_interval", 5)
        self.max_poll_attempts = self.retry_config.get("max_poll_attempts", 240)
        self.max_poll_records = 50
        self._cancel_flag = False
        self._create_response = None
        self._poll_attempts: List[Dict[str, Any]] = []
        self.api_config = channel_config.get("api_config", {
            "text_path": "/api/v3/chat/completions",
            "image_path": "/api/v3/responses",
            "video_path": "/api/v3/contents/generations/tasks",
            "text_stream": False,
        })

    async def convert_params(
        self,
        model_config: Dict[str, Any],
        params: Dict[str, Any],
        endpoint_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """将平台参数转换为火山引擎格式 - 支持视频和多模态文本/图片"""

        # 视频：多模态 content[]（文/图/视频/音频），统一走 _build_video_body
        is_video = (
            is_volcengine_video_endpoint(endpoint_config, category=params.get("category", ""))
            or params.get("is_video")
            or params.get("category") == "video"
        )

        if is_video:
            return self._build_video_body(params)

        # 其他类型（文本/图片）：使用兼容 OpenAI 的标准 body 结构
        body: Dict[str, Any] = {
            "model": params.get("model") or model_config.get("channel_model_id") or "",
            "input": params.get("prompt", ""),
        }

        # 常见可选参数
        for key in ("temperature", "top_p", "top_k", "max_tokens", "seed"):
            if key in params:
                body[key] = params[key]

        # 多模态输入（图片/视频作为参考）
        messages: List[Dict[str, Any]] = []
        has_multimodal = False

        raw_imgs: List[str] = []
        if "images" in params and isinstance(params["images"], list):
            for img in params["images"]:
                u = extract_url_from_image_item(img) if isinstance(img, dict) else img
                if u:
                    raw_imgs.append(u)
        if "image" in params and isinstance(params["image"], list):
            for img in params["image"]:
                u = extract_url_from_image_item(img) if isinstance(img, dict) else img
                if u:
                    raw_imgs.append(u)

        if raw_imgs:
            has_multimodal = True
            parts: List[Dict[str, Any]] = []
            if params.get("prompt"):
                parts.append({"type": "text", "text": params["prompt"]})
            for u in raw_imgs:
                cdn_url = require_cdn_url(u, label="参考图")
                parts.append({"type": "image_url", "image_url": {"url": cdn_url}})
            messages.append({"role": "user", "content": parts})

        # 若为 chat 端点，使用 messages 字段
        if endpoint_config and "chat" in str(endpoint_config.get("endpoint", "")).lower():
            if messages:
                body["messages"] = messages
            elif params.get("prompt"):
                body["messages"] = [
                    {"role": "user", "content": params["prompt"]}
                ]
            # chat 格式不需要 input 字段
            body.pop("input", None)
        elif has_multimodal and not messages:
            # 非 chat 但有图片，仍然附加 image_urls 到 body
            body["image_urls"] = raw_imgs

        logger.info(f"[{self.trace_id}] convert_params - category={'video' if is_video else 'text/image'}, "
                    f"keys={list(body.keys())}")
        return body

    def _build_video_body(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """构建视频生成 body（content + 各种媒体字段）"""
        content: List[Dict[str, Any]] = []
        if params.get("prompt"):
            content.append({"type": "text", "text": params["prompt"]})

        if params.get("images") and isinstance(params["images"], list):
            for i, img in enumerate(params["images"]):
                url = extract_url_from_image_item(img) if isinstance(img, dict) else img
                if url:
                    cdn_url = require_cdn_url(url, label=f"参考图[{i + 1}]")
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": cdn_url},
                        "role": "reference_image",
                    })

        if params.get("videos") and isinstance(params["videos"], list):
            for video in params["videos"]:
                url = video.get("url") if isinstance(video, dict) else video
                if url:
                    content.append({
                        "type": "video_url",
                        "video_url": {"url": url},
                        "role": "reference_video",
                    })

        if params.get("audios") and isinstance(params["audios"], list):
            for audio in params["audios"]:
                url = audio.get("url") if isinstance(audio, dict) else audio
                if url:
                    content.append({
                        "type": "audio_url",
                        "audio_url": {"url": url},
                        "role": "reference_audio",
                    })

        result: Dict[str, Any] = {
            "content": content,
            "generate_audio": params.get("audio", True),
            "ratio": params.get("ratio", "adaptive"),
            "duration": params.get("duration", 5),
            "watermark": params.get("watermark", False),
        }
        if params.get("video_quality"):
            result["video_quality"] = params["video_quality"]
        return result

    def _finalize_volcengine_video_body(
        self,
        body: Dict[str, Any],
        channel_params: Dict[str, Any],
        channel_model_id: str,
    ) -> Dict[str, Any]:
        """
        body_params 未命中（如 curl 导入把固定值误标为 dynamic）时，
        用 convert_params / _build_video_body 的结果兜底，避免空 body。
        """
        shaped = (
            channel_params
            if channel_params.get("content")
            else self._build_video_body(channel_params)
        )
        merged: Dict[str, Any] = {**shaped, **(body or {})}
        if not merged.get("model"):
            merged["model"] = channel_model_id
        if not merged.get("content"):
            merged["content"] = shaped.get("content", [])
        return merged

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

        safe_headers = {k: v if k.lower() != "authorization" else "Bearer ***" for k, v in headers.items()}
        self._http_request_info = {
            "method": "POST",
            "url": url,
            "headers": safe_headers,
            "body": body,
            "timestamp": time.time(),
        }

        await self._flush_outgoing_request_log()

        logger.info(f"[{self.trace_id}] ═════════ POST {url}")
        try:
            safe_body = {k: v for k, v in body.items() if k != "api_key"}
            logger.info(f"[{self.trace_id}] body={json.dumps(safe_body, ensure_ascii=False, indent=2, default=str)[:800]}")
        except Exception:
            pass

        last_error: Optional[Exception] = None
        max_retries = self.retry_config.get("max_retries", 1)

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=body, headers=headers)

                logger.info(f"[{self.trace_id}] HTTP {response.status_code} 响应 (attempt {attempt + 1})")

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

                    if response.status_code == 401:
                        raise Exception(f"401 Unauthorized - API Key 无效或过期 (渠道响应: {err_msg})")
                    elif response.status_code == 429:
                        raise Exception(f"429 Too Many Requests - 超出频率限制或配额不足 (渠道响应: {err_msg})")
                    elif response.status_code >= 500:
                        raise Exception(f"{response.status_code} Server Error (渠道响应: {err_msg})")
                    else:
                        raise Exception(f"HTTP {response.status_code}: {err_msg}")
            except Exception as e:
                last_error = e
                logger.warning(f"[{self.trace_id}] HTTP 请求失败 (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = self.retry_config.get("retry_delay", 2)
                    time.sleep(wait_time)

        raise last_error or Exception("HTTP 请求失败")

    async def call_api(
        self,
        category: str,
        channel_params: Dict[str, Any],
        channel_model_id: str,
        api_key: str,
        endpoint_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """调用火山引擎 API

        优先级：
        1. 有 endpoint_config → 走 _call_dynamic_api（根据端点配置）
        2. 无 endpoint_config → 根据 category 使用默认路径
        """
        # 从端点配置读取 content_type / headers
        content_type = "application/json"
        extra_headers: Dict[str, str] = {}
        if endpoint_config:
            ct = endpoint_config.get("content_type") or endpoint_config.get("content-type") or endpoint_config.get("body_type")
            if ct:
                content_type = ct
            h = endpoint_config.get("headers")
            if isinstance(h, dict):
                extra_headers = {str(k): str(v) for k, v in h.items()}

        if endpoint_config and endpoint_config.get("endpoint"):
            logger.info(
                f"[{self.trace_id}] 使用端点配置: type={endpoint_config.get('type')}, "
                f"endpoint={endpoint_config.get('endpoint')}, content_type={content_type}"
            )
            return await self._call_dynamic_api(
                category, channel_params, channel_model_id, api_key, endpoint_config,
                content_type, extra_headers,
            )

        # 回落：按 category 使用默认路径
        path_map = {
            "text": self.api_config.get("text_path", "/api/v3/chat/completions"),
            "chat": self.api_config.get("text_path", "/api/v3/chat/completions"),
            "image": self.api_config.get("image_path", "/api/v3/responses"),
            "image_edits": self.api_config.get("image_path", "/api/v3/responses"),
            "video": self.api_config.get("video_path", "/api/v3/contents/generations/tasks"),
            "video_image": self.api_config.get("video_path", "/api/v3/contents/generations/tasks"),
        }
        path = path_map.get(category, "/api/v3/chat/completions")
        url = join_url(self.base_url, path)

        body = {"model": channel_model_id, **channel_params}

        logger.info(f"[{self.trace_id}] call_api(默认) - category={category}, base_url={self.base_url}, model={channel_model_id}")

        if category == "video":
            return await self._call_video_async(url, body, api_key, content_type, extra_headers)

        return await self._http_post(url, body, api_key, content_type, extra_headers)

    async def _call_dynamic_api(
        self,
        category: str,
        channel_params: Dict[str, Any],
        channel_model_id: str,
        api_key: str,
        endpoint_config: Dict[str, Any],
        content_type: str = "application/json",
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """根据端点配置动态调用 API - 与配置引擎打通"""
        endpoint_type = endpoint_config.get("type", category)
        endpoint_path = endpoint_config.get("endpoint", "")
        method = endpoint_config.get("method", "POST").upper()
        extra_headers = extra_headers or {}

        if not endpoint_path:
            logger.warning(f"[{self.trace_id}] 端点缺少 endpoint 字段，回落")
            if category == "video":
                return await self._call_video_async(
                    join_url(self.base_url, self.api_config.get("video_path", "/api/v3/contents/generations/tasks")),
                    {"model": channel_model_id, **channel_params},
                    api_key,
                )
            return await self._http_post(
                join_url(self.base_url, self.api_config.get("text_path", "/api/v3/chat/completions")),
                {"model": channel_model_id, **channel_params},
                api_key,
            )

        url = join_url(self.base_url, endpoint_path)

        # 使用配置引擎构建请求体（新的 body_params 或 旧的 params_template）
        has_template = (
            endpoint_config.get("body_params")
            or endpoint_config.get("params_template")
            or endpoint_config.get("param_mappings")
        )
        if has_template:
            logger.info(f"[{self.trace_id}] 使用配置引擎构建请求体 - type={endpoint_type}")
            body = ConfigEngine.build_request_body(
                endpoint_config=endpoint_config,
                params=channel_params,
                model_id=channel_model_id,
                channel_code=self.channel_code,
                trace_id=self.trace_id,
            )
            if is_volcengine_video_endpoint(endpoint_config, category=category):
                body = self._finalize_volcengine_video_body(
                    body, channel_params, channel_model_id
                )
        else:
            logger.info(f"[{self.trace_id}] 动态端点调用(无模板) - type={endpoint_type}, path={endpoint_path}")
            body = {"model": channel_model_id, **channel_params}

        logger.info(f"[{self.trace_id}] URL={url}, method={method}, content_type={content_type}")

        # 视频端点走异步任务模式（video / video_image / 多模态槽位）
        if (
            endpoint_type in ("video", "video_image")
            or is_volcengine_video_endpoint(endpoint_config, category=category)
            or "contents/generations/tasks" in endpoint_path
        ):
            return await self._call_video_async(url, body, api_key, content_type, extra_headers)

        if method == "POST":
            return await self._http_post(url, body, api_key, content_type, extra_headers)
        elif method == "GET":
            query_url = url + "?" + "&".join(
                [f"{k}={v}" for k, v in body.items() if isinstance(v, (str, int, float))]
            )
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                get_headers: Dict[str, str] = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": content_type,
                }
                get_headers.update(extra_headers)
                resp = await client.get(query_url, headers=get_headers)
                if resp.status_code == 200:
                    return resp.json()
                raise Exception(f"HTTP {resp.status_code}: {resp.text[:300]}")
        else:
            raise Exception(f"不支持的 HTTP 方法: {method}")

    async def _call_video_async(self, url: str, body: Dict[str, Any], api_key: str,
                                 content_type: str = "application/json",
                                 extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """视频生成异步调用：创建任务 + 轮询状态"""
        extra_headers = extra_headers or {}
        logger.info(f"[{self.trace_id}] 开始视频异步生成流程")

        # 步骤1: 创建任务
        logger.info(f"[{self.trace_id}] 步骤1 - 创建视频生成任务")
        create_response = await self._http_post(url, body, api_key, content_type, extra_headers)

        task_id = create_response.get("id") or create_response.get("task_id")
        if not task_id:
            raise Exception(f"创建任务失败：未返回任务ID")

        logger.info(f"[{self.trace_id}] 任务创建成功，task_id={task_id}")

        self._create_response = create_response
        await self._persist_external_task_id(task_id)

        # 步骤2: 轮询任务状态
        logger.info(f"[{self.trace_id}] 步骤2 - 开始轮询任务状态")
        status_url = f"{url}/{task_id}"

        # 轮询 GET 用 headers
        poll_headers: Dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": content_type,
        }
        poll_headers.update(extra_headers)

        for attempt in range(self.max_poll_attempts):
            if self._cancel_flag:
                logger.info(f"[{self.trace_id}] 轮询被手动停止")
                raise Exception("视频生成任务被用户手动停止")

            poll_start = time.time()
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(status_url, headers=poll_headers)

                    if response.status_code == 200:
                        task_result = response.json()
                        status = task_result.get("status")
                        duration_ms = int((time.time() - poll_start) * 1000)

                        self._poll_attempts.append({
                            "attempt": attempt + 1,
                            "status": status,
                            "http_status": response.status_code,
                            "duration_ms": duration_ms,
                            "timestamp": datetime.now().isoformat(),
                            "progress": task_result.get("progress"),
                        })
                        if len(self._poll_attempts) > self.max_poll_records:
                            half = self.max_poll_records // 2
                            self._poll_attempts = self._poll_attempts[:half] + self._poll_attempts[-half:]

                        logger.info(f"[{self.trace_id}] 轮询第 {attempt + 1} 次 - 状态: {status}, 耗时: {duration_ms}ms")

                        if status == "succeeded":
                            logger.info(f"[{self.trace_id}] 任务完成！")
                            return task_result
                        elif status == "failed":
                            error_msg = task_result.get("error", {}).get("message", "任务失败")
                            raise Exception(f"视频生成任务失败: {error_msg}")
                        elif status in ("running", "queued"):
                            await asyncio.sleep(self.poll_interval)
                        else:
                            await asyncio.sleep(self.poll_interval)
                    else:
                        duration_ms = int((time.time() - poll_start) * 1000)
                        self._poll_attempts.append({
                            "attempt": attempt + 1,
                            "status": "poll_error",
                            "http_status": response.status_code,
                            "duration_ms": duration_ms,
                            "timestamp": datetime.now().isoformat(),
                        })
                        if len(self._poll_attempts) > self.max_poll_records:
                            half = self.max_poll_records // 2
                            self._poll_attempts = self._poll_attempts[:half] + self._poll_attempts[-half:]
                        logger.warning(f"[{self.trace_id}] 轮询失败 HTTP {response.status_code}")
                        await asyncio.sleep(self.poll_interval)
            except Exception as e:
                duration_ms = int((time.time() - poll_start) * 1000)
                self._poll_attempts.append({
                    "attempt": attempt + 1,
                    "status": "exception",
                    "http_status": None,
                    "duration_ms": duration_ms,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)[:200],
                })
                if len(self._poll_attempts) > self.max_poll_records:
                    half = self.max_poll_records // 2
                    self._poll_attempts = self._poll_attempts[:half] + self._poll_attempts[-half:]
                logger.warning(f"[{self.trace_id}] 轮询异常: {e}")
                await asyncio.sleep(self.poll_interval)

        raise Exception(f"视频生成任务超时（超过 {self.max_poll_attempts * self.poll_interval} 秒）")

    def cancel(self):
        """取消轮询任务"""
        logger.info(f"[{self.trace_id}] 设置取消标志")
        self._cancel_flag = True

    async def parse_result(
        self,
        category: str,
        raw_result: Dict[str, Any],
        endpoint_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """将火山引擎响应转换为平台统一格式"""
        response = raw_result.get("response", raw_result) if isinstance(raw_result, dict) else raw_result
        result: Dict[str, Any] = {}

        # 视频生成结果
        if category == "video":
            content = response.get("content", {}) if isinstance(response, dict) else {}
            video_url = content.get("video_url") if isinstance(content, dict) else None
            if video_url:
                result["videos"] = [{
                    "url": video_url,
                    "width": response.get("width"),
                    "height": response.get("height"),
                    "duration": response.get("duration"),
                }]
                return result

        # 文本对话 / responses 格式
        if isinstance(response, dict):
            # 格式 A: { "output": { "choices": [ { "text": "..." } ] } }
            outputs = response.get("output", {}).get("choices", []) if isinstance(response.get("output"), dict) else []
            if outputs and isinstance(outputs, list):
                output = outputs[0]
                if category == "text" or (endpoint_config and endpoint_config.get("type") in ("text", "chat")):
                    text = output.get("text") or output.get("content") or ""
                    if text:
                        result["text"] = text
                elif category in ("image", "image_edits") or (endpoint_config and endpoint_config.get("type") in ("image", "image_edits")):
                    image_url = output.get("image_url") or output.get("url")
                    if image_url:
                        result["images"] = [{
                            "url": image_url,
                            "width": output.get("width"),
                            "height": output.get("height"),
                        }]

            # 格式 B: OpenAI 标准 responses 响应
            if not result and "choices" in response:
                choices = response["choices"]
                if isinstance(choices, list) and choices:
                    first = choices[0]
                    # messages/content 形式
                    message = first.get("message", {}) if isinstance(first, dict) else {}
                    content = message.get("content") if isinstance(message, dict) else None
                    if content and isinstance(content, str):
                        result["text"] = content
                    # content 为多模态列表
                    elif isinstance(content, list):
                        text_parts = [c.get("text") for c in content if isinstance(c, dict) and c.get("text")]
                        if text_parts:
                            result["text"] = "\n".join(text_parts)
                        img_parts = [c.get("image_url", {}).get("url") for c in content if isinstance(c, dict) and isinstance(c.get("image_url"), dict)]
                        if img_parts:
                            result["images"] = [{"url": u} for u in img_parts if u]

            # 格式 C: { "data": [ { "url": "..." } ] } (OpenAI 图片格式)
            if not result and "data" in response and isinstance(response["data"], list):
                if category in ("image", "image_edits"):
                    images = [{"url": item.get("url")} for item in response["data"] if isinstance(item, dict) and item.get("url")]
                    if images:
                        result["images"] = images

        if not result and isinstance(response, dict):
            if response.get("result"):
                result["text"] = str(response["result"])

        logger.info(f"[{self.trace_id}] parse_result - category={category}, result_keys={list(result.keys())}")
        return result

    def parse_error(self, exception: Exception) -> tuple[str, str]:
        """将异常转换为统一错误码和消息"""
        msg = str(exception)
        if "401" in msg or "Unauthorized" in msg:
            return "auth_error", "API Key 无效或过期"
        elif "429" in msg or "Too Many Requests" in msg:
            return "rate_limit", "请求过于频繁，请稍后重试"
        elif "500" in msg or "Server Error" in msg:
            return "server_error", "服务端错误，请稍后重试"
        else:
            return "channel_error", msg[:200]

    async def query_task(self, external_task_id: str) -> Dict[str, Any]:
        """查询外部任务状态（用于服务器重启后恢复任务）"""
        api_key = self.get_api_key_for_category("video")
        if not api_key:
            return {"success": False, "error_code": "auth_error", "error_message": "API Key 未配置"}

        path = self.api_config.get("video_path", "/api/v3/contents/generations/tasks")
        status_url = join_url(self.base_url, f"{path}/{external_task_id}")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"[{self.trace_id}] 查询外部任务状态: {status_url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(status_url, headers=headers)

                if response.status_code == 200:
                    task_result = response.json()
                    status = task_result.get("status")

                    if status == "succeeded":
                        result = await self.parse_result("video", task_result)
                        return {"success": True, "data": result, "status": "completed"}
                    elif status == "failed":
                        error_msg = task_result.get("error", {}).get("message", "任务失败")
                        return {"success": False, "error_code": "task_failed", "error_message": error_msg, "status": "failed"}
                    elif status in ("running", "queued"):
                        return {"success": False, "status": "running", "message": "任务仍在运行中"}
                    else:
                        return {"success": False, "status": "unknown", "message": f"未知状态: {status}"}
                else:
                    try:
                        err_json = response.json()
                        err_msg = err_json.get("message", f"HTTP {response.status_code}")
                    except Exception:
                        err_msg = response.text[:200]
                    return {"success": False, "error_code": "http_error", "error_message": err_msg}
        except Exception as e:
            logger.error(f"[{self.trace_id}] 查询外部任务失败: {e}")
            return {"success": False, "error_code": "query_failed", "error_message": str(e)}
