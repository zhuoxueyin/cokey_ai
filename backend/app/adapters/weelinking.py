from __future__ import annotations

from typing import Any, Dict
import time
import json

from openai import AsyncOpenAI
from app.adapters.base import BaseChannelAdapter
from app.core.logging_config import get_logger

logger = get_logger()


class WeelinkingAdapter(BaseChannelAdapter):
    def __init__(self, channel_config: Dict[str, Any], trace_id: str):
        super().__init__(channel_config, trace_id)
        self.client = None

    async def convert_params(self, model_config: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        return params

    async def call_api(self, category: str, channel_params: Dict[str, Any], channel_model_id: str, api_key: str) -> Dict[str, Any]:
        logger.info(f"[{self.trace_id}] call_api - category={category}, base_url={self.base_url}, model={channel_model_id}, api_key_len={len(api_key) if api_key else 0}")
        
        if not api_key:
            raise Exception(f"渠道 API Key 未配置: category={category}, channel={self.channel_code}")
        
        self_client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=api_key,
            timeout=self.retry_config.get("timeout", 60),
        )

        if category == "text":
            prompt = channel_params.get("prompt", "")
            messages = channel_params.get("messages")

            if not messages:
                messages = [
                    {"role": "system", "content": "你是一个有帮助的助手"},
                    {"role": "user", "content": prompt if prompt else "你好"},
                ]
            elif messages and not messages[-1].get("content"):
                messages = [
                    {"role": "system", "content": "你是一个有帮助的助手"},
                    {"role": "user", "content": prompt if prompt else "你好"},
                ]

            kwargs: Dict[str, Any] = {
                "model": channel_model_id,
                "messages": messages,
                "stream": True,
            }
            if "temperature" in channel_params:
                kwargs["temperature"] = float(channel_params["temperature"])
            if "max_tokens" in channel_params:
                kwargs["max_tokens"] = int(channel_params["max_tokens"])
            if "seed" in channel_params:
                kwargs["seed"] = int(channel_params["seed"])

            _body_for_log = {k: v for k, v in kwargs.items() if k != "stream"}
            _body_for_log["stream"] = True
            logger.info(f"[{self.trace_id}] ═══════ API 完整请求体 ═══════")
            logger.info(f"[{self.trace_id}] POST {self.base_url}/chat/completions (stream)")
            logger.info(f"[{self.trace_id}] Authorization: Bearer ...{api_key[-8:] if api_key else 'NULL'}")
            try:
                logger.info(f"[{self.trace_id}] body=\n{json.dumps({k: v for k, v in kwargs.items() if k != 'stream'}, ensure_ascii=False, indent=2)}")
            except Exception as _e:
                logger.info(f"[{self.trace_id}] body_raw={_body_for_log}")
            logger.info(f"[{self.trace_id}] ════════════════════════════════")

            collected_chunks = []
            full_text = ""
            async for chunk in await self_client.chat.completions.create(**kwargs):
                chunk_dict = chunk.model_dump() if hasattr(chunk, "model_dump") else {}
                collected_chunks.append(chunk_dict)
                choices = chunk_dict.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        full_text += content
            
            logger.info(f"[{self.trace_id}] 流式调用完成, 共 {len(collected_chunks)} 个 chunk, 文本长度={len(full_text)}")

            return {
                "type": "text",
                "response": {
                    "id": collected_chunks[0].get("id", "") if collected_chunks else "",
                    "object": "chat.completion",
                    "model": channel_model_id,
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": full_text,
                        },
                        "finish_reason": "stop",
                    }],
                    "usage": {},
                },
                "stream_chunks": collected_chunks,
            }

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
