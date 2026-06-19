"""Weelinking GPT Image 2 请求规范化（对齐 gpt_image_2_demo.py）"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

# demo.py 文档列出的常用尺寸
WEELINKING_DEMO_SIZES = frozenset({
    "1024x1024",
    "1536x1024",
    "1024x1536",
    "auto",
})

# 比例 → demo 兼容尺寸（1k 档优先使用渠道文档尺寸）
WEELINKING_RATIO_TO_SIZE: Dict[str, str] = {
    "1:1": "1024x1024",
    "3:2": "1536x1024",
    "2:3": "1024x1536",
    "4:3": "1536x1024",
    "3:4": "1024x1536",
    "5:4": "1024x1024",
    "4:5": "1024x1536",
    "16:9": "1536x1024",
    "9:16": "1024x1536",
    "2:1": "1536x1024",
    "1:2": "1024x1536",
    "3:1": "1536x1024",
    "1:3": "1024x1536",
    "21:9": "1536x1024",
    "9:21": "1024x1536",
}

# 非 demo 尺寸 → 最近兼容尺寸
WEELINKING_SIZE_ALIASES: Dict[str, str] = {
    "864x1536": "1024x1536",
    "1536x864": "1536x1024",
    "768x1024": "1024x1536",
    "1024x768": "1536x1024",
    "608x1088": "1024x1536",
    "1280x1024": "1024x1024",
    "1024x1280": "1024x1536",
}


def is_gpt_image_model(model_id: str) -> bool:
    return "gpt-image" in (model_id or "").lower()


def sanitize_image_prompt(prompt: str) -> str:
    """去掉 markdown 代码块包裹，保留正文（避免模板符号干扰渠道）"""
    if not prompt:
        return prompt
    text = prompt.strip()
    # 去掉 ```lang ... ``` 围栏
    text = re.sub(r"```[\w]*\s*", "", text)
    text = text.replace("```", "")
    # 去掉 **标题** 标记
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    # 合并多余空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_weelinking_gpt_image_body(
    body: Dict[str, Any],
    channel_params: Optional[Dict[str, Any]] = None,
    *,
    endpoint: str = "generations",
) -> Dict[str, Any]:
    """
    文生图 generations：model, prompt, size, quality, output_format, background, n
    图生图 edits：对齐官方 curl，额外 response_format / output_compression 等
    """
    model = str(body.get("model", ""))
    if not is_gpt_image_model(model):
        return body

    params = channel_params or {}
    out = dict(body)
    is_edits = endpoint in ("edits", "image_edits")

    if is_edits:
        quality = out.get("quality") or params.get("quality")
        out["quality"] = "high" if not quality or quality == "auto" else str(quality)
        out["response_format"] = str(
            params.get("response_format") or out.get("response_format") or "url"
        )
        bg = out.get("background") or params.get("background")
        out["background"] = "opaque" if not bg or bg == "auto" else str(bg)
    else:
        quality = out.get("quality") or params.get("quality")
        if not quality or quality == "auto":
            out["quality"] = "auto"
        else:
            out["quality"] = str(quality)
        out.setdefault("background", "auto")

    out.setdefault("output_format", "png")

    # Weelinking /images/generations 不使用 resolution；有像素 size 时不传 aspect_ratio
    out.pop("resolution", None)

    raw_size = str(out.get("size") or params.get("size") or "").strip().lower()
    aspect_ratio = str(out.get("aspect_ratio") or params.get("aspect_ratio") or "").strip()

    if raw_size and raw_size != "auto" and "x" in raw_size:
        mapped = WEELINKING_SIZE_ALIASES.get(raw_size, raw_size)
        if mapped not in WEELINKING_DEMO_SIZES and aspect_ratio in WEELINKING_RATIO_TO_SIZE:
            mapped = WEELINKING_RATIO_TO_SIZE[aspect_ratio]
        out["size"] = mapped
        out.pop("aspect_ratio", None)
    elif aspect_ratio in WEELINKING_RATIO_TO_SIZE:
        out["size"] = WEELINKING_RATIO_TO_SIZE[aspect_ratio]
        out.pop("aspect_ratio", None)
    elif not out.get("size"):
        out["size"] = "1024x1024"

    if "prompt" in out:
        out["prompt"] = sanitize_image_prompt(str(out["prompt"]))

    if is_edits:
        out_fmt = str(out.get("output_format", "png")).lower()
        if out_fmt in ("png", "jpeg", "jpg", "webp"):
            comp = params.get("output_compression") or out.get("output_compression")
            out["output_compression"] = int(comp if comp is not None else 90)
        user_val = params.get("user") or params.get("trace_id") or out.get("user")
        if user_val:
            out["user"] = str(user_val)[:128]
        out.pop("n", None)
    else:
        for key in ("response_format", "thinking", "stream", "output_compression", "user"):
            out.pop(key, None)

    return out
