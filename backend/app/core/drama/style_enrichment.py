"""风格封面与提示词增强。"""
from __future__ import annotations

from typing import Dict, List

_TAG_EN: Dict[str, str] = {
    "科幻": "sci-fi, futuristic technology",
    "复古": "retro vintage aesthetic",
    "古风": "traditional Chinese historical",
    "权谋": "political intrigue, court drama",
    "冷峻": "cold tone, high contrast shadows",
    "悬疑": "mystery suspense, noir atmosphere",
    "国产": "Chinese cinematic look",
    "冷调": "cool color grading, desaturated blues",
    "古偶": "ancient romance, ethereal beauty",
    "唯美": "dreamy aesthetic, soft beauty",
    "柔光": "soft diffused lighting, glow",
    "日系": "Japanese film aesthetic",
    "青春": "youthful coming-of-age",
    "胶片": "35mm film grain, analog texture",
    "生活": "everyday life, naturalistic",
    "自然": "natural lighting, organic colors",
    "韩剧": "K-drama cinematic look",
    "都市": "urban modern cityscape",
    "写实": "photorealistic, documentary realism",
    "武侠": "wuxia martial arts, flowing robes",
    "摄影": "professional photography, sharp focus",
    "90年代": "1990s retro film look",
    "电影": "cinematic widescreen composition",
    "赛博": "cyberpunk neon",
    "霓虹": "neon lights, rain-soaked streets",
    "暗黑": "dark moody, low-key lighting",
    "奇幻": "fantasy magical, otherworldly",
    "仙侠": "xianxia immortal cultivation",
    "宫廷": "palace imperial grandeur",
    "民国": "Republic of China era vintage",
    "港风": "Hong Kong cinema golden age",
    "欧美": "Hollywood cinematic",
    "蒸汽朋克": "steampunk brass gears",
    "原子朋克": "atompunk retro-futurism",
    "末世": "post-apocalyptic wasteland",
    "废土": "wasteland survival gritty",
    "校园": "school campus youth",
    "职场": "workplace professional drama",
    "甜宠": "sweet romance, warm pastel",
    "虐恋": "melodramatic angst, emotional contrast",
    "重生": "rebirth revenge drama tension",
    "穿越": "time travel fantasy fusion",
    "宫斗": "palace intrigue scheming",
    "热血": "dynamic action energy",
    "运动": "sports dynamic motion",
    "美食": "food photography appetizing",
    "旅行": "travel scenic vistas",
    "音乐": "musical rhythm visual sync",
    "舞蹈": "dance movement fluid",
    "AIGC": "AI generated art polish",
    "anime": "anime cel-shaded",
    "漫剧": "comic panel narrative",
    "3D": "3D CGI render",
    "国风": "Chinese aesthetic, traditional Eastern art direction",
    "神话": "Chinese mythology, divine beings and legendary tales",
    "仙侠": "xianxia immortal cultivation, flowing robes, sword flight",
    "玄幻": "Chinese fantasy xuanhuan, epic magical worldbuilding",
    "2D": "2D flat illustration",
    "platform": "social media vertical format",
    "film": "film grain cinematic",
    "sound": "synesthetic audio-visual mood",
}


def tags_to_en_prompt(tags: List[str]) -> str:
    parts: List[str] = []
    for t in tags:
        if t in _TAG_EN:
            parts.append(_TAG_EN[t])
        else:
            parts.append(t)
    return ", ".join(dict.fromkeys(parts))


def style_cover_url(style_id: str, width: int = 400, height: int = 533) -> str:
    return f"https://picsum.photos/seed/{style_id}/{width}/{height}"
