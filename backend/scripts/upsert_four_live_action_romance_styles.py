"""将国产悬疑冷调、古偶唯美柔光、韩剧都市柔光、日式青春胶片 详细描述写入 MongoDB 并发布。"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import close_mongodb, init_mongodb
from app.core.drama.style_description_catalog import get_style_description_md
from app.services.drama_style_service import get_drama_style_service

STYLE_IDS = (
    "cn_suspense_cold_tone",
    "ancient_romance_soft_glow",
    "kdrama_urban_soft",
    "jp_youth_film",
)


async def main() -> None:
    await init_mongodb()
    svc = get_drama_style_service()

    for style_id in STYLE_IDS:
        doc = await svc.get_by_style_id(style_id)
        if not doc:
            print(f"[!] 风格不存在: {style_id}")
            continue

        name = doc.get("name") or style_id
        render_class = doc.get("render_class") or "live_action"
        tags = doc.get("genre_tags") or []
        md = get_style_description_md(style_id, name, render_class, tags)
        if not md:
            print(f"[!] catalog 无 Markdown: {style_id}")
            continue

        updated = await svc.update(style_id, {"style_description_md": md})
        if not updated:
            print(f"[!] update 失败: {style_id}")
            continue

        try:
            published = await svc.publish(style_id)
            status = "published"
        except ValueError as e:
            published = updated
            status = f"updated_draft ({e})"

        mp = published.get("model_prompts") or {}
        print(f"[ok] {style_id} · {name}")
        print(f"     status={status}")
        print(f"     md_len={len(md)}")
        print(f"     style_summary_zh={(mp.get('style_summary_zh') or '')[:100]}…")
        print(f"     image_positive_en={(mp.get('image_positive_en') or '')[:140]}…")
        print()

    await close_mongodb()


if __name__ == "__main__":
    asyncio.run(main())
