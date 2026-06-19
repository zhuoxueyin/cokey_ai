"""
配置化引擎 - 统一的参数模板解析和请求构建引擎
目标：通过配置化实现零硬编码的渠道接入
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Union

from app.core.logging_config import get_logger
from app.core.body_param_resolver import build_body_from_params
from app.core.cdn import extract_url_from_image_item, require_cdn_url

logger = get_logger()


class ConfigEngine:
    """统一配置引擎

    核心能力:
    1. 模板变量替换: {prompt}, {model}, {channel_code}
    2. 参数映射规则: param_mappings 实现字段重命名、类型转换、CDN处理
    3. 默认参数合并: default_params + 传入参数
    4. 必填参数校验: required_params
    5. 响应内容提取: response_extract_path / response_mappings
    """

    # 预定义变量
    BUILTIN_VARS = {"prompt", "model", "channel_code", "trace_id", "n", "seed"}

    @classmethod
    def build_request_body(
        cls,
        endpoint_config: Dict[str, Any],
        params: Dict[str, Any],
        model_id: str,
        channel_code: str = "",
        trace_id: str = "",
    ) -> Dict[str, Any]:
        """构建请求体 - 统一入口

        优先级：
          1. body_params（新格式，入参表）
          2. params_template + param_mappings（旧格式，保持兼容）
          3. 直接使用传入 params

        Args:
            endpoint_config: 端点配置对象
            params: 业务传入参数
            model_id: 模型ID
            channel_code: 渠道编码
            trace_id: 跟踪ID

        Returns:
            构建完成的请求体
        """
        if not endpoint_config:
            return params

        # 1. body_params 新格式 —— 优先级最高
        body_params = endpoint_config.get("body_params") or []
        if body_params:
            body = build_body_from_params(
                body_params,
                params,
                model_id=model_id,
                channel_code=channel_code,
                trace_id=trace_id,
            )
            logger.info(f"[{trace_id}] body_params 构建完成: {list(body.keys())}")
            return body

        # 2. 旧格式 params_template + param_mappings（保持兼容）
        params_template = endpoint_config.get("params_template") or {}
        body: Dict[str, Any] = {}

        template_vars = cls._collect_template_vars(
            params, model_id, channel_code, trace_id
        )

        default_params = endpoint_config.get("default_params") or {}
        merged_params = {**default_params, **params}

        if params_template:
            body = cls._render_template(params_template, template_vars, merged_params)
            logger.info(f"[{trace_id}] 模板渲染完成: {list(body.keys())}")
        else:
            body = dict(merged_params)
            logger.info(f"[{trace_id}] 无参数模板，使用原始参数: {list(body.keys())}")

        param_mappings = endpoint_config.get("param_mappings") or []
        if param_mappings:
            mapped_body = cls._apply_mappings(
                param_mappings, merged_params, template_vars, trace_id
            )
            body.update(mapped_body)
            logger.info(f"[{trace_id}] 映射规则应用完成，新增字段: {list(mapped_body.keys())}")

        required_params = endpoint_config.get("required_params") or []
        if required_params:
            missing = [p for p in required_params if not cls._get_nested_field(body, p)]
            if missing:
                raise Exception(f"缺少必填参数: {missing}")

        logger.info(f"[{trace_id}] 最终请求体 keys: {list(body.keys())}")
        return body

    @classmethod
    def _smart_parse_fixed_value(cls, raw: str) -> Any:
        """智能解析固定值：
        - 空字符串 → 空字符串
        - "true" / "false" → 布尔
        - 纯数字字符串 → 整数 / 浮点
        - 以 { 或 [ 开头的字符串 → 尝试 JSON 解析
        - 其他 → 原字符串
        """
        if raw is None:
            return None
        if not isinstance(raw, str):
            return raw

        s = raw.strip()
        if not s:
            return ""

        lower = s.lower()
        if lower in ("true", "false"):
            return lower == "true"

        if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
            try:
                return int(s)
            except ValueError:
                pass

        try:
            if s[0] in "{[":
                return json.loads(s)
            float(s)
            return float(s)
        except (ValueError, json.JSONDecodeError):
            pass

        return raw

    @classmethod
    def parse_response(
        cls,
        endpoint_config: Dict[str, Any],
        response: Dict[str, Any],
        endpoint_type: str,
        trace_id: str = "",
    ) -> Dict[str, Any]:
        """解析响应 - 配置化响应映射

        Args:
            endpoint_config: 端点配置
            response: 原始响应
            endpoint_type: 端点类型
            trace_id: 跟踪ID

        Returns:
            统一格式的响应
        """
        if not endpoint_config:
            return {"type": endpoint_type, "raw": response}

        # 1. 如果配置了 response_extract_path，直接提取内容
        extract_path = endpoint_config.get("response_extract_path")
        if extract_path:
            extracted = cls._get_nested_field(response, extract_path)
            if extracted:
                return {"type": endpoint_type, "content": extracted, "raw": response}

        # 2. 如果配置了 response_mappings，按映射规则解析
        response_mappings = endpoint_config.get("response_mappings") or []
        if response_mappings:
            return cls._apply_response_mappings(
                response_mappings, response, endpoint_type, trace_id
            )

        # 3. 无配置时，根据端点类型返回原始响应
        return {"type": endpoint_type, "raw": response}

    # ==================== 内部工具方法 ====================

    @classmethod
    def _collect_template_vars(
        cls,
        params: Dict[str, Any],
        model_id: str,
        channel_code: str,
        trace_id: str,
    ) -> Dict[str, Any]:
        """收集模板变量"""
        return {
            "prompt": params.get("prompt", ""),
            "model": model_id or params.get("model", ""),
            "channel_code": channel_code,
            "trace_id": trace_id,
            "n": params.get("n", params.get("count", 1)),
            "seed": params.get("seed", 0),
        }

    @classmethod
    def _render_template(
        cls,
        template: Any,
        template_vars: Dict[str, Any],
        params: Dict[str, Any],
    ) -> Any:
        """递归渲染模板

        支持的模板语法:
        - "{prompt}"  → 简单变量替换
        - "{images.0.url}" → 嵌套字段提取
        """
        if isinstance(template, str):
            # 检查是否是 "{xxx}" 完整占位符
            if re.match(r"^\{[\w\.]+}$", template):
                var_name = template[1:-1]
                # 优先从 template_vars 取，其次从 params
                if var_name in template_vars:
                    return template_vars[var_name]
                val = cls._get_nested_field(params, var_name)
                if val is not None:
                    return val
                return template
            # 部分替换：如 "User: {prompt}"
            result = template
            for key, value in template_vars.items():
                result = result.replace("{" + key + "}", str(value) if value else "")
            return result

        if isinstance(template, dict):
            return {
                key: cls._render_template(value, template_vars, params)
                for key, value in template.items()
            }

        if isinstance(template, list):
            return [
                cls._render_template(item, template_vars, params) for item in template
            ]

        return template

    @classmethod
    def _apply_mappings(
        cls,
        mappings: List[Dict[str, Any]],
        params: Dict[str, Any],
        template_vars: Dict[str, Any],
        trace_id: str,
    ) -> Dict[str, Any]:
        """应用参数映射规则

        支持的 transform:
        - "first_image": 取第一张图片的URL
        - "image_list": 转换为图片列表，自动CDN处理
        - "int": 转整数
        - "float": 转浮点
        - "str": 转字符串
        - "json": JSON 字符串解析
        - "cdn_url": 确保是 CDN URL
        """
        result: Dict[str, Any] = {}

        for mapping in mappings:
            source = mapping.get("source", "")
            target = mapping.get("target", source)
            default = mapping.get("default")
            transform = mapping.get("transform")

            # 从 params 或 template_vars 获取值
            value = cls._get_nested_field(params, source)
            if value is None and source in template_vars:
                value = template_vars[source]
            if value is None:
                value = default

            if value is None:
                continue

            # 应用转换规则
            try:
                if transform == "first_image":
                    value = cls._extract_first_image(value, trace_id)
                elif transform == "image_list":
                    value = cls._extract_image_list(value, trace_id)
                elif transform == "cdn_url":
                    value = cls._ensure_cdn_url(value, trace_id)
                elif transform == "int":
                    value = int(value) if value != "" else 0
                elif transform == "float":
                    value = float(value) if value != "" else 0.0
                elif transform == "str":
                    value = str(value)
                elif transform == "json":
                    if isinstance(value, str):
                        value = json.loads(value)
            except Exception as e:
                logger.warning(f"[{trace_id}] 转换失败 {transform}: {e}")

            # 设置到目标字段（支持多级如 "inputs.image"）
            cls._set_nested_field(result, target, value)

        return result

    @classmethod
    def _apply_response_mappings(
        cls,
        mappings: List[Dict[str, Any]],
        response: Dict[str, Any],
        endpoint_type: str,
        trace_id: str,
    ) -> Dict[str, Any]:
        """应用响应映射规则"""
        images: List[Dict[str, Any]] = []
        videos: List[Dict[str, Any]] = []
        audios: List[Dict[str, Any]] = []
        text_content = ""

        for mapping in mappings:
            source = mapping.get("source", "")
            content_type = mapping.get("content_type", "text")

            value = cls._get_nested_field(response, source)
            if value is None:
                continue

            if content_type == "text":
                if isinstance(value, str):
                    text_content = value
            elif content_type == "image":
                if isinstance(value, str):
                    images.append({"url": value, "revised_prompt": ""})
                elif isinstance(value, list):
                    for item in value:
                        url = item.get("url") if isinstance(item, dict) else str(item)
                        if url:
                            images.append({"url": url, "revised_prompt": item.get("revised_prompt", "") if isinstance(item, dict) else ""})
            elif content_type == "video":
                if isinstance(value, str):
                    videos.append({"url": value, "revised_prompt": ""})
                elif isinstance(value, list):
                    for item in value:
                        url = item.get("url") if isinstance(item, dict) else str(item)
                        if url:
                            videos.append({"url": url, "revised_prompt": item.get("revised_prompt", "") if isinstance(item, dict) else ""})
            elif content_type == "audio":
                if isinstance(value, str):
                    audios.append({"url": value})
                elif isinstance(value, list):
                    for item in value:
                        url = item.get("url") if isinstance(item, dict) else str(item)
                        if url:
                            audios.append({"url": url})

        # 返回统一格式
        if endpoint_type in ("image", "image_edits") and images:
            return {"type": "image", "images": images, "count": len(images)}
        elif endpoint_type in ("video", "video_image") and videos:
            return {"type": "video", "videos": videos, "count": len(videos)}
        elif endpoint_type == "audio" and audios:
            return {"type": "audio", "audios": audios, "count": len(audios)}
        elif text_content:
            return {"type": "text", "text": text_content}

        return {"type": endpoint_type, "raw": response}

    # ==================== 辅助方法 ====================

    @staticmethod
    def _get_nested_field(obj: Any, path: str) -> Any:
        """从嵌套对象中按路径获取值，如 'data.0.url'"""
        if not path:
            return obj
        keys = path.split(".")
        current = obj
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list):
                try:
                    current = current[int(key)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return current

    @staticmethod
    def _set_nested_field(obj: Dict[str, Any], path: str, value: Any) -> None:
        """设置嵌套字段，如 path='inputs.image' -> obj['inputs']['image'] = value"""
        keys = path.split(".")
        current = obj
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    @staticmethod
    def _extract_first_image(value: Any, trace_id: str) -> Optional[str]:
        """从多种格式中提取第一张图片的URL，确保是CDN URL"""
        if not value:
            return None

        try:
            if isinstance(value, str):
                url = value.strip()
                return require_cdn_url(url, label="参考图") if url else None

            if isinstance(value, list) and len(value) > 0:
                first = value[0]
                if isinstance(first, str):
                    return require_cdn_url(first.strip(), label="参考图") if first else None
                if isinstance(first, dict):
                    url = extract_url_from_image_item(first)
                    if isinstance(url, str) and url:
                        return require_cdn_url(url, label="参考图")
            return None
        except Exception as e:
            logger.warning(f"[{trace_id}] 提取第一张图片失败: {e}")
            return None

    @staticmethod
    def _extract_image_list(value: Any, trace_id: str) -> List[str]:
        """从多种格式中提取图片列表，确保都是CDN URL"""
        if not value:
            return []

        items = []
        try:
            if isinstance(value, str):
                items = [value]
            elif isinstance(value, list):
                items = value[:16]  # 限制最多16张

            result = []
            for i, item in enumerate(items):
                if not item:
                    continue
                url = extract_url_from_image_item(item) if not isinstance(item, str) else item
                if isinstance(url, str) and url.strip():
                    cdn_url = require_cdn_url(url.strip(), label=f"参考图[{i+1}]")
                    result.append(cdn_url)
            return result
        except Exception as e:
            logger.warning(f"[{trace_id}] 提取图片列表失败: {e}")
            return []

    @staticmethod
    def _ensure_cdn_url(value: Any, trace_id: str) -> Optional[str]:
        """确保URL是CDN地址"""
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            return require_cdn_url(value.strip(), label="资源URL")
        except Exception as e:
            logger.warning(f"[{trace_id}] CDN URL转换失败: {e}")
            return value


# ==================== 预设模板库 ====================
PRESET_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "openai_completions": {
        "description": "OpenAI 兼容文本生成",
        "params_template": {
            "model": "{model}",
            "messages": [{"role": "user", "content": "{prompt}"}],
            "stream": False,
        },
        "response_extract_path": "choices.0.message.content",
        "endpoint_type": "text",
    },
    "openai_images_generations": {
        "description": "OpenAI 兼容文生图",
        "params_template": {
            "model": "{model}",
            "prompt": "{prompt}",
            "n": "{n}",
            "size": "1024x1024",
        },
        "response_mappings": [
            {"source": "data", "content_type": "image"}
        ],
        "endpoint_type": "image",
    },
    "chat_with_images": {
        "description": "对话式（支持多模态图文输入）",
        "params_template": {
            "model": "{model}",
            "messages": [
                {"role": "user", "content": "{prompt}"}
            ],
        },
        "param_mappings": [
            {"source": "images", "target": "messages.0.content", "transform": None, "default": None}
        ],
        "response_extract_path": "choices.0.message.content",
        "endpoint_type": "chat",
    },
}


def get_preset_template(name: str) -> Optional[Dict[str, Any]]:
    """获取预设模板"""
    return PRESET_TEMPLATES.get(name)
