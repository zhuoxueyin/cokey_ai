from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from app.adapters.weelinking import WeelinkingAdapter
from app.core.apiyi_image import (
    build_apiyi_chat_image_body,
    collect_reference_image_urls,
    extract_images_from_markdown,
    is_apiyi_conversational_image_model,
    resolve_image_count,
)
from app.core.apiyi_vip_image import (
    APIYI_VIP_EDITS_IMAGE_FIELD,
    build_apiyi_vip_edits_form_fields,
    build_apiyi_vip_generations_body,
    is_apiyi_vip_image_model,
)
from app.core.chat_image_protocol import is_openai_chat_image_slot
from app.core.cdn import is_cdn_url
from app.core.logging_config import get_logger
from app.utils.url_utils import join_url

logger = get_logger()


class ApiyiAdapter(WeelinkingAdapter):
    """APIYI 渠道适配器
    - gpt-image-2-all / gpt-image-2-vip → 对话式 Chat Completions（主推）
    - gpt-image-2-vip 可选 Images API（generations / edits）由协议画像 endpoint_type 决定
    """

    def _should_use_apiyi_chat_image(
        self, endpoint_config: Optional[Dict[str, Any]]
    ) -> bool:
        """对话式 vs Images API：由 protocol_slot 或端点 type 决定，默认走对话式。"""
        if endpoint_config:
            if is_openai_chat_image_slot(endpoint_config.get("protocol_slot")):
                return True
            ep_type = endpoint_config.get("type", "")
            if ep_type == "chat":
                return True
            if ep_type in ("image", "image_edits"):
                return False
        return True

    async def call_api(
        self,
        category: str,
        channel_params: Dict[str, Any],
        channel_model_id: str,
        api_key: str,
        endpoint_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        chat_image_slot = endpoint_config and is_openai_chat_image_slot(
            endpoint_config.get("protocol_slot")
        )
        if (
            is_apiyi_conversational_image_model(channel_model_id)
            and (category == "image" or chat_image_slot)
            and self._should_use_apiyi_chat_image(endpoint_config)
        ):
            return await self._call_gpt_image_chat_api(
                channel_params, channel_model_id, api_key, endpoint_config
            )
        if category == "image" and is_apiyi_vip_image_model(channel_model_id):
            refs = collect_reference_image_urls(channel_params)
            if refs:
                return await self._call_gpt_image_vip_edits_api(
                    channel_params, channel_model_id, api_key, endpoint_config
                )
            return await self._call_gpt_image_vip_api(
                channel_params, channel_model_id, api_key, endpoint_config
            )
        return await super().call_api(
            category, channel_params, channel_model_id, api_key, endpoint_config
        )

    async def _call_gpt_image_chat_api(
        self,
        channel_params: Dict[str, Any],
        channel_model_id: str,
        api_key: str,
        endpoint_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        chat_endpoint = self._get_endpoint_by_type("chat") or endpoint_config
        path = "/chat/completions"
        if chat_endpoint and chat_endpoint.get("endpoint"):
            path = chat_endpoint["endpoint"]
        elif self.api_config.get("text_path"):
            path = self.api_config["text_path"]

        url = join_url(self.base_url, path)
        target_n = resolve_image_count(channel_params)

        self._active_category = "image"
        ref_count = len(collect_reference_image_urls(channel_params))
        logger.info(
            f"[{self.trace_id}] APIYI 对话式生图 model={channel_model_id} "
            f"refs={ref_count} target_n={target_n} url={url}"
        )

        if target_n <= 1:
            body = build_apiyi_chat_image_body(channel_params, channel_model_id)
            response = await self._http_post(url, body, api_key)
            return {"type": "chat", "response": response}

        collected: list[Dict[str, str]] = []
        seen_urls: set[str] = set()
        last_response: Optional[Dict[str, Any]] = None
        base_prompt = str(channel_params.get("prompt") or "")

        for index in range(target_n):
            params = dict(channel_params)
            params["n"] = 1
            if index == 0:
                params["prompt"] = base_prompt
            else:
                params["prompt"] = (
                    f"{base_prompt}（共{target_n}张中的第{index + 1}张，"
                    f"请与前几张风格一致但画面需有明显差异）"
                ).strip()
            body = build_apiyi_chat_image_body(params, channel_model_id)
            last_response = await self._http_post(url, body, api_key)
            content = self._extract_chat_message_content(last_response)
            for img in extract_images_from_markdown(content):
                img_url = img.get("url") or ""
                if img_url and img_url not in seen_urls:
                    seen_urls.add(img_url)
                    collected.append(img)
            if len(collected) >= target_n:
                break

        if not collected:
            return {"type": "chat", "response": last_response or {}}

        combined_content = "\n\n".join(
            f"![image]({img['url']})" for img in collected[:target_n]
        )
        synthetic = dict(last_response or {})
        choices = list(synthetic.get("choices") or [{}])
        first = dict(choices[0]) if choices else {}
        message = dict(first.get("message") or {})
        message["content"] = combined_content
        first["message"] = message
        if choices:
            choices[0] = first
        else:
            choices = [first]
        synthetic["choices"] = choices
        logger.info(
            f"[{self.trace_id}] APIYI 对话式生图合并 {len(collected[:target_n])}/{target_n} 张"
        )
        return {"type": "chat", "response": synthetic}

    @staticmethod
    def _extract_chat_message_content(response: Dict[str, Any]) -> str:
        choices = response.get("choices") or []
        if not choices:
            return ""
        msg = choices[0].get("message") or {}
        content = msg.get("content") or ""
        if not content and choices[0].get("delta"):
            content = choices[0]["delta"].get("content") or ""
        return content if isinstance(content, str) else ""

    async def _call_gpt_image_vip_api(
        self,
        channel_params: Dict[str, Any],
        channel_model_id: str,
        api_key: str,
        endpoint_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        image_endpoint = self._get_endpoint_by_type("image") or endpoint_config
        path = "/images/generations"
        if image_endpoint and image_endpoint.get("endpoint"):
            path = image_endpoint["endpoint"]
        elif self.api_config.get("image_path"):
            path = self.api_config["image_path"]

        url = join_url(self.base_url, path)
        body = build_apiyi_vip_generations_body(channel_params, channel_model_id)

        self._active_category = "image"
        logger.info(
            f"[{self.trace_id}] APIYI gpt-image-2-vip 文生图 "
            f"size={body.get('size')} url={url}"
        )

        response = await self._http_post(url, body, api_key)
        return {"type": "image", "response": response}

    async def _call_gpt_image_vip_edits_api(
        self,
        channel_params: Dict[str, Any],
        channel_model_id: str,
        api_key: str,
        endpoint_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """APIYI VIP 图生图 / 多图融合 — POST /v1/images/edits"""
        edits_endpoint = self._get_endpoint_by_type("image_edits") or endpoint_config
        path = "/images/edits"
        if edits_endpoint and edits_endpoint.get("endpoint"):
            path = edits_endpoint["endpoint"]

        url = join_url(self.base_url, path)
        text_fields = build_apiyi_vip_edits_form_fields(channel_params, channel_model_id)

        refs = collect_reference_image_urls(channel_params)
        image_bytes_list = []
        for i, img_url in enumerate(refs[:16]):
            try:
                img_bytes, _ = await self._download_image_bytes(
                    img_url, label=f"参考图[{i + 1}]"
                )
                image_bytes_list.append(img_bytes)
            except Exception as e:
                logger.warning(f"[{self.trace_id}] VIP 参考图下载失败，跳过: {e}")

        if not image_bytes_list:
            raise Exception("图生图需要至少一张参考图，请上传 CDN 图片后重试")

        image_fields = {APIYI_VIP_EDITS_IMAGE_FIELD: image_bytes_list}

        self._active_category = "image"
        logger.info(
            f"[{self.trace_id}] APIYI gpt-image-2-vip 图生图 "
            f"size={text_fields.get('size')} images={len(image_bytes_list)} "
            f"field={APIYI_VIP_EDITS_IMAGE_FIELD} url={url}"
        )

        response = await self._http_post_multipart(
            url, text_fields, image_fields, api_key
        )
        return {"type": "image_edits", "response": response}

    async def _ensure_image_url(self, url: str) -> str:
        from app.services.storage_service import get_storage_service

        storage = get_storage_service()
        if not storage.enabled:
            return url

        try:
            if url.startswith("data:"):
                header, encoded = url.split(",", 1)
                content_type = "image/png"
                if ";" in header and ":" in header:
                    content_type = header.split(":")[1].split(";")[0]
                import base64

                data = base64.b64decode(encoded)
                ext = ".png" if "png" in content_type else ".jpg"
                uploaded = await storage.upload_generated_image(
                    data, f"apiyi_{self.trace_id[:8]}{ext}", content_type
                )
                return uploaded or url

            if url.startswith("https://") and not is_cdn_url(url):
                async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                    resp = await client.get(url)
                if resp.status_code == 200 and resp.content:
                    content_type = resp.headers.get("content-type", "image/png")
                    ext = ".png" if "png" in content_type else ".jpg"
                    uploaded = await storage.upload_generated_image(
                        resp.content, f"apiyi_{self.trace_id[:8]}{ext}", content_type
                    )
                    return uploaded or url
        except Exception as e:
            logger.warning(f"[{self.trace_id}] 图片转平台 CDN 失败: {e}")
        return url

    async def parse_result(
        self,
        category: str,
        raw_result: Dict[str, Any],
        endpoint_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        result_type = raw_result.get("type", category)

        if category == "image" and result_type in ("chat", "text"):
            response = raw_result.get("response") or {}
            choices = response.get("choices") or []
            content = ""
            if choices:
                msg = choices[0].get("message") or {}
                content = msg.get("content") or ""
                if not content and choices[0].get("delta"):
                    content = choices[0]["delta"].get("content") or ""

            images = extract_images_from_markdown(content)
            if images:
                processed = []
                for img in images:
                    final_url = await self._ensure_image_url(img["url"])
                    processed.append({"url": final_url, "revised_prompt": ""})
                logger.info(f"[{self.trace_id}] APIYI 从 Markdown 解析到 {len(processed)} 张图")
                return {"type": "image", "images": processed, "count": len(processed)}

            if content:
                logger.warning(
                    f"[{self.trace_id}] APIYI chat 响应未解析到图片 Markdown，content 前 200 字: {content[:200]}"
                )

        if category == "image" and result_type in ("image", "image_edits"):
            response = raw_result.get("response") or {}
            image_data = response.get("data") or []
            images = []
            for item in image_data:
                if not isinstance(item, dict):
                    continue
                img_url = item.get("url")
                if not img_url and item.get("b64_json"):
                    img_url = await self._ensure_image_url(item["b64_json"])
                if img_url:
                    images.append({"url": img_url, "revised_prompt": item.get("revised_prompt", "")})
            if images:
                return {"type": "image", "images": images, "count": len(images)}

        return await super().parse_result(category, raw_result, endpoint_config)
