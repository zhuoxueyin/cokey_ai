"""图像模型官方尺寸标准（与 PROTOCOL_SPEC.md §2.3.1、frontend imageSizeSpec.ts 同步）"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ImageSizePreset:
    aspect_ratio: str
    clarity: str
    width: int
    height: int

    @property
    def size(self) -> str:
        return f"{self.width}x{self.height}"


def _p(ratio: str, clarity: str, w: int, h: int) -> ImageSizePreset:
    return ImageSizePreset(aspect_ratio=ratio, clarity=clarity, width=w, height=h)


# GPT Image 2 官方映射
GPT_IMAGE_2_PRESETS: List[ImageSizePreset] = [
    _p("1:1", "1k", 1024, 1024),
    _p("1:1", "2k", 2048, 2048),
    _p("1:1", "4k", 2880, 2880),
    _p("3:2", "1k", 1536, 1024),
    _p("3:2", "2k", 2048, 1360),
    _p("3:2", "4k", 3520, 2336),
    _p("2:3", "1k", 1024, 1536),
    _p("2:3", "2k", 1360, 2048),
    _p("2:3", "4k", 2336, 3520),
    _p("4:3", "1k", 1024, 768),
    _p("4:3", "2k", 2048, 1536),
    _p("4:3", "4k", 3312, 2480),
    _p("3:4", "1k", 768, 1024),
    _p("3:4", "2k", 1536, 2048),
    _p("3:4", "4k", 2480, 3312),
    _p("5:4", "1k", 1280, 1024),
    _p("5:4", "2k", 2560, 2048),
    _p("5:4", "4k", 3216, 2576),
    _p("4:5", "1k", 1024, 1280),
    _p("4:5", "2k", 2048, 2560),
    _p("4:5", "4k", 2576, 3216),
    _p("16:9", "1k", 1536, 1024),
    _p("16:9", "2k", 2048, 1152),
    _p("16:9", "4k", 3840, 2160),
    _p("9:16", "1k", 1024, 1536),
    _p("9:16", "2k", 1152, 2048),
    _p("9:16", "4k", 2160, 3840),
    _p("2:1", "1k", 2048, 1024),
    _p("2:1", "2k", 2688, 1344),
    _p("2:1", "4k", 3840, 1920),
    _p("1:2", "1k", 1024, 2048),
    _p("1:2", "2k", 1344, 2688),
    _p("1:2", "4k", 1920, 3840),
    _p("3:1", "1k", 1881, 836),
    _p("3:1", "2k", 3072, 1024),
    _p("3:1", "4k", 3840, 1280),
    _p("1:3", "1k", 887, 1774),
    _p("1:3", "2k", 1024, 3072),
    _p("1:3", "4k", 1280, 3840),
    _p("21:9", "1k", 2016, 864),
    _p("21:9", "2k", 2688, 1152),
    _p("21:9", "4k", 3840, 1648),
    _p("9:21", "1k", 864, 2016),
    _p("9:21", "2k", 1152, 2688),
    _p("9:21", "4k", 1648, 3840),
]

DALL_E_3_PRESETS: List[ImageSizePreset] = [
    _p("1:1", "1k", 1024, 1024),
    _p("9:16", "1k", 1024, 1792),
    _p("16:9", "1k", 1792, 1024),
]

MODEL_SIZE_SPECS: Dict[str, List[ImageSizePreset]] = {
    "gpt-image-2": GPT_IMAGE_2_PRESETS,
    "dall-e-3": DALL_E_3_PRESETS,
}

MODEL_MATCH_PATTERNS: List[Tuple[str, List[str]]] = [
    ("gpt-image-2", ["gpt-image-2-all", "gpt-image-2-vip", "gpt-image-2", "gpt-image", "gpt_image"]),
    ("dall-e-3", ["dall-e-3", "dalle-3", "dall_e_3"]),
]

_SIZE_LOOKUP: Dict[str, Dict[str, ImageSizePreset]] = {}
for spec_id, presets in MODEL_SIZE_SPECS.items():
    _SIZE_LOOKUP[spec_id] = {p.size: p for p in presets}


def resolve_spec_id(model_code: str = "", channel_model_id: str = "") -> str:
    haystack = f"{channel_model_id} {model_code}".lower()
    for spec_id, patterns in MODEL_MATCH_PATTERNS:
        if any(p in haystack for p in patterns):
            return spec_id
    return "gpt-image-2"


def get_presets(model_code: str = "", channel_model_id: str = "") -> List[ImageSizePreset]:
    spec_id = resolve_spec_id(model_code, channel_model_id)
    return MODEL_SIZE_SPECS.get(spec_id, GPT_IMAGE_2_PRESETS)


def normalize_image_size(
    params: Dict,
    model_code: str = "",
    channel_model_id: str = "",
) -> Tuple[Dict, Optional[str]]:
    """校验并规范化图像尺寸参数，返回 (新 params, 错误信息)"""
    spec_id = resolve_spec_id(model_code, channel_model_id)
    allowed = _SIZE_LOOKUP.get(spec_id, _SIZE_LOOKUP["gpt-image-2"])
    presets = MODEL_SIZE_SPECS.get(spec_id, GPT_IMAGE_2_PRESETS)

    size = str(params.get("size", "")).strip().lower()
    aspect_ratio = str(params.get("aspect_ratio", "")).strip()
    resolution = str(params.get("resolution", "")).strip().lower()

    if size in allowed:
        preset = allowed[size]
        normalized = dict(params)
        normalized["size"] = preset.size
        normalized["aspect_ratio"] = preset.aspect_ratio
        if spec_id == "gpt-image-2":
            normalized["resolution"] = preset.clarity
        return normalized, None

    if aspect_ratio and resolution:
        for p in presets:
            if p.aspect_ratio == aspect_ratio and p.clarity == resolution:
                normalized = dict(params)
                normalized["size"] = p.size
                normalized["aspect_ratio"] = p.aspect_ratio
                normalized["resolution"] = p.clarity
                return normalized, None
        return params, f"不支持的尺寸组合: {aspect_ratio} @ {resolution}"

    if size:
        allowed_list = ", ".join(sorted(allowed.keys())[:8])
        return params, f"尺寸 {size} 不在模型 {spec_id} 官方列表中（示例: {allowed_list}...）"

    return params, None
