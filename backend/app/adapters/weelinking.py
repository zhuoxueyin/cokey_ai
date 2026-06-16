from __future__ import annotations

from typing import Any, Dict, List
import time
import json
import urllib.parse

import httpx

from app.adapters.base import BaseChannelAdapter
from app.core.logging_config import get_logger

logger = get_logger()


def _join_url(base_url: str, path: str) -> str:
    """将 base_url 与 path 拼接成完整 URL
    base_url 可能带 / 或 /v1/ 后缀，需要保证路径正确。
    """
    base = base_url.rstrip("/")
    rel = path.lstrip("/")
    return f"{base}/{rel}"


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
        self.api_config = channel_config.get("api_config", {
            "text_path": "/chat/completions",
            "image_path": "/images/generations",
            "video_path": "/videos/generations",
            "text_stream": True,
        })

    async def convert_params(self, model_config: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        return params

    async def _http_post(self, url: str, body: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        """统一 HTTP POST 请求，带重试和日志"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"[{self.trace_id}] ═════════ POST {url}")
        try:
            safe_body = {k: v for k, v in body.items() if k != "api_key"}
            logger.info(f"[{self.trace_id}] body={json.dumps(safe_body, ensure_ascii=False, indent=2)[:500]}")
        except Exception:
            pass

        last_error = None
        max_retries = self.retry_config.get("max_retries", 1)

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
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
                        err_msg = json.dumps(err_json, ensure_ascii=False, indent=2)
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
                logger.warning(f"[{self.trace_id}] HTTP 请求失败 (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = self.retry_config.get("retry_delay", 2)
                    time.sleep(wait_time)

        raise last_error or Exception("HTTP 请求失败")

    async def _http_post_stream(self, url: str, body: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        """流式 HTTP POST 请求，处理 stream=True 的响应"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
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
                async with httpx.AsyncClient(timeout=self.timeout) as client:
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
                logger.warning(f"[{self.trace_id}] 流式请求失败 (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = self.retry_config.get("retry_delay", 2)
                    time.sleep(wait_time)

        raise last_error or Exception("流式 HTTP 请求失败")

    async def call_api(self, category: str, channel_params: Dict[str, Any], channel_model_id: str, api_key: str) -> Dict[str, Any]:
        logger.info(f"[{self.trace_id}] call_api - category={category}, base_url={self.base_url}, model={channel_model_id}")

        if not api_key:
            raise Exception(f"渠道 API Key 未配置: category={category}, channel={self.channel_code}")

        if category == "text":
            return await self._call_text_api(channel_params, channel_model_id, api_key)
        elif category == "image":
            return await self._call_image_api(channel_params, channel_model_id, api_key)
        elif category == "video":
            return await self._call_video_api(channel_params, channel_model_id, api_key)
        else:
            raise Exception(f"不支持的分类: {category}")

    async def _call_text_api(self, channel_params: Dict[str, Any], channel_model_id: str, api_key: str) -> Dict[str, Any]:
        """文本生成：POST /chat/completions
        
        支持图片输入（vision）和流式响应配置
        """
        text_path = self.api_config.get("text_path", "/chat/completions")
        url = _join_url(self.base_url, text_path)
        prompt = channel_params.get("prompt", "")
        messages = channel_params.get("messages")
        images = channel_params.get("images", [])

        if not messages:
            content: List[Dict[str, Any]] = []
            
            # 添加文本提示
            if prompt:
                content.append({"type": "text", "text": prompt})
            
            # 添加图片（支持多张）
            for img in images:
                # 支持字符串格式和对象格式 {"url": "...", "file_name": "..."}
                img_url = img.get("url") if isinstance(img, dict) else img
                if isinstance(img_url, str):
                    if img_url.startswith("http"):
                        content.append({"type": "image_url", "image_url": {"url": img_url}})
                    elif img_url.startswith("data:"):
                        content.append({"type": "image_url", "image_url": {"url": img_url}})
            
            messages = [
                {"role": "system", "content": "你是一个有帮助的助手"},
                {"role": "user", "content": content if content else prompt if prompt else "你好"},
            ]
        elif messages and not messages[-1].get("content"):
            content: List[Dict[str, Any]] = []
            if prompt:
                content.append({"type": "text", "text": prompt})
            for img in images:
                # 支持字符串格式和对象格式 {"url": "...", "file_name": "..."}
                img_url = img.get("url") if isinstance(img, dict) else img
                if isinstance(img_url, str):
                    if img_url.startswith("http"):
                        content.append({"type": "image_url", "image_url": {"url": img_url}})
                    elif img_url.startswith("data:"):
                        content.append({"type": "image_url", "image_url": {"url": img_url}})
            
            messages = [
                {"role": "system", "content": "你是一个有帮助的助手"},
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
        """图片生成：POST /images/generations

        请求体格式（与 gpt-image-2-demo.py 对齐）：
        {
            "model": "gpt-image-2",
            "prompt": "...",
            "size": "1024x1024",
            "quality": "auto",        # auto/low/medium/high
            "output_format": "png",   # png/jpeg/webp
            "background": "auto",     # auto/transparent/opaque
            "n": 1,                   # 最多 4
            "negative_prompt": "...",
            "seed": 123456,
            "images": [...]           # 参考图片URL列表
        }
        """
        image_path = self.api_config.get("image_path", "/images/generations")
        url = _join_url(self.base_url, image_path)
        prompt = channel_params.get("prompt", "")

        body: Dict[str, Any] = {
            "model": channel_model_id,
            "prompt": prompt,
            "size": "1024x1024",
            "n": 1,
        }
        if "negative_prompt" in channel_params:
            body["negative_prompt"] = str(channel_params["negative_prompt"])
        if "n" in channel_params:
            body["n"] = max(1, min(4, int(channel_params["n"])))
        elif "count" in channel_params:
            body["n"] = max(1, min(4, int(channel_params["count"])))
        if "size" in channel_params:
            body["size"] = str(channel_params["size"])
        if "quality" in channel_params:
            body["quality"] = str(channel_params["quality"])
        if "background" in channel_params:
            body["background"] = str(channel_params["background"])
        if "seed" in channel_params:
            body["seed"] = int(channel_params["seed"])
        # 添加参考图片支持
        if "images" in channel_params and isinstance(channel_params["images"], list):
            # 提取图片URL（支持对象格式和字符串格式）
            image_urls = []
            for img in channel_params["images"]:
                if isinstance(img, str):
                    image_urls.append(img)
                elif isinstance(img, dict) and img.get("url"):
                    image_urls.append(img["url"])
            if image_urls:
                body["images"] = image_urls[:6]  # 最多支持6张参考图

        response = await self._http_post(url, body, api_key)
        return {"type": "image", "response": response}

    async def _call_video_api(self, channel_params: Dict[str, Any], channel_model_id: str, api_key: str) -> Dict[str, Any]:
        """视频生成：POST /videos/generations"""
        video_path = self.api_config.get("video_path", "/videos/generations")
        url = _join_url(self.base_url, video_path)
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
        try:
            import base64
            from app.services.storage_service import get_storage_service
            from datetime import datetime
            
            # 解码base64数据
            image_data = base64.b64decode(base64_data)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}.png"
            
            # 上传到GitHub
            storage = get_storage_service()
            if not storage.enabled:
                logger.warning(f"[{self.trace_id}] 存储服务未启用，无法上传图片")
                return None
            
            url = await storage.upload_generated_image(image_data, filename, "image/png")
            if url:
                logger.info(f"[{self.trace_id}] 图片上传成功: {url}")
                return url
            else:
                logger.warning(f"[{self.trace_id}] 图片上传失败")
                return None
        except Exception as e:
            logger.error(f"[{self.trace_id}] 上传base64图片异常: {e}")
            return None

    async def parse_result(self, category: str, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        if raw_result.get("type") == "text":
            response = raw_result["response"]
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

        elif raw_result.get("type") == "image":
            response = raw_result["response"]
            image_data = response.get("data", [])
            images = []
            for item in image_data:
                img_url = item.get("url")
                if not img_url and item.get("b64_json"):
                    # 将base64图片上传到GitHub存储，获取URL
                    uploaded_url = await self._upload_base64_image(item["b64_json"])
                    if uploaded_url:
                        img_url = uploaded_url
                    else:
                        # 回退方案：使用base64格式（但会被task_service截断）
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

        elif raw_result.get("type") == "video":
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
                    videos.append({
                        "url": item.get("url"),
                        "revised_prompt": item.get("revised_prompt", ""),
                    })
            return {
                "type": "video",
                "videos": videos,
                "count": len(videos),
            }

        return {"type": "unknown", "raw": raw_result}

    def parse_error(self, exception: Exception) -> tuple[str, str]:
        err_msg = str(exception).lower()

        if "401" in err_msg or "unauthorized" in err_msg or "invalid" in err_msg and "key" in err_msg:
            return "channel_error", "渠道鉴权失败，请检查API密钥"
        elif "429" in err_msg or "rate" in err_msg or "quota" in err_msg or "frequency" in err_msg:
            return "service_unavailable", "模型服务繁忙，请稍后再试"
        elif "timeout" in err_msg or "timed out" in err_msg:
            return "timeout", "生成超时，请稍后重试"
        elif "content_policy" in err_msg or "safety" in err_msg or "violation" in err_msg:
            return "content_violation", "内容不符合规范，请调整提示词"
        elif "not_found" in err_msg or "404" in err_msg or "not found" in err_msg:
            return "channel_error", "模型不存在或已下线"
        elif "500" in err_msg or "502" in err_msg or "503" in err_msg or "server" in err_msg:
            return "service_unavailable", "服务暂不可用"
        else:
            return "internal_error", f"生成失败: {str(exception)[:200]}"
