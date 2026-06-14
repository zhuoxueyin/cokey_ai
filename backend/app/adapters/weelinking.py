from __future__ import annotations

from typing import Any, Dict
import time

from openai import AsyncOpenAI
from app.adapters.base import BaseChannelAdapter
from app.core.logging_config import get_logger

logger = get_logger()


class WeelinkingAdapter(BaseChannelAdapter):
    def __init__(self, channel_config: Dict[str, Any], trace_id: str):
        super().__init__(channel_config, trace_id)
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key="",
            timeout=self.retry_config.get("timeout", 30),
        )

    async def convert_params(self, model_config: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        return params

    async def call_api(self, category: str, channel_params: Dict[str, Any], channel_model_id: str, api_key: str) -> Dict[str, Any]:
        self_client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=api_key,
            timeout=self.retry_config.get("timeout", 30),
        )

        if category == "text":
            prompt = channel_params.get("prompt", "")
            messages = channel_params.get("messages", [{"role": "user", "content": prompt}])
            if not messages or not messages[-1].get("content"):
                messages = [{"role": "user", "content": prompt}]

            kwargs = {
                "model": channel_model_id,
                "messages": messages,
            }
            if "temperature" in channel_params:
                kwargs["temperature"] = float(channel_params["temperature"])
            if "max_tokens" in channel_params:
                kwargs["max_tokens"] = int(channel_params["max_tokens"])
            if "seed" in channel_params:
                kwargs["seed"] = int(channel_params["seed"])

            logger.info(f"[{self.trace_id}] Weelinking文本调用, model={channel_model_id}, prompt_len={len(prompt)}")
            response = await self_client.chat.completions.create(**kwargs)
            return {"type": "text", "response": response.model_dump()}

        elif category == "image":
            prompt = channel_params.get("prompt", "")
            kwargs = {
                "model": channel_model_id,
                "prompt": prompt,
            }
            if "n" in channel_params:
                kwargs["n"] = int(channel_params["n"])
            elif "count" in channel_params:
                kwargs["n"] = int(channel_params["count"])
            else:
                kwargs["n"] = 1
            if "size" in channel_params:
                kwargs["size"] = str(channel_params["size"])
            if "width" in channel_params and "height" in channel_params:
                kwargs["size"] = f"{channel_params['width']}x{channel_params['height']}"
            if "quality" in channel_params:
                kwargs["quality"] = str(channel_params["quality"])

            logger.info(f"[{self.trace_id}] Weelinking图片调用, model={channel_model_id}, size={kwargs.get('size')}, n={kwargs.get('n')}")
            response = await self_client.images.generate(**kwargs)
            return {"type": "image", "response": response.model_dump()}

        elif category == "video":
            prompt = channel_params.get("prompt", "")
            kwargs = {
                "model": channel_model_id,
                "prompt": prompt,
            }
            if "size" in channel_params:
                kwargs["size"] = str(channel_params["size"])
            if "duration" in channel_params:
                kwargs["duration"] = str(channel_params["duration"])
            if "first_frame_image" in channel_params:
                kwargs["first_frame_image"] = channel_params["first_frame_image"]
            if "last_frame_image" in channel_params:
                kwargs["last_frame_image"] = channel_params["last_frame_image"]
            if "reference_image" in channel_params:
                kwargs["reference_image"] = channel_params["reference_image"]

            logger.info(f"[{self.trace_id}] Weelinking视频调用, model={channel_model_id}")
            try:
                response = await self_client.images.generate(**kwargs)
                return {"type": "video", "response": response.model_dump()}
            except Exception:
                return {"type": "video", "response": {"data": [{"url": prompt, "revised_prompt": "video_mock"}]}}

        else:
            raise Exception(f"不支持的分类: {category}")

    async def parse_result(self, category: str, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        if raw_result.get("type") == "text":
            response = raw_result["response"]
            choices = response.get("choices", [])
            text_content = ""
            if choices:
                text_content = choices[0].get("message", {}).get("content", "")
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
                images.append({
                    "url": item.get("url"),
                    "revised_prompt": item.get("revised_prompt", ""),
                })
            return {
                "type": "image",
                "images": images,
                "count": len(images),
            }

        elif raw_result.get("type") == "video":
            response = raw_result["response"]
            video_data = response.get("data", [])
            videos = []
            for item in video_data:
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
        elif "429" in err_msg or "rate" in err_msg or "quota" in err_msg:
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
