"""将上美画风（american_boom_era）增强描述写入 MongoDB 并发布。"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import close_mongodb, init_mongodb
from app.core.drama.style_description_catalog import get_style_description_md
from app.services.drama_style_service import get_drama_style_service

STYLE_ID = "american_boom_era"


async def main() -> None:
    await init_mongodb()
    svc = get_drama_style_service()
    doc = await svc.get_by_style_id(STYLE_ID)
    if not doc:
        print(f"[!] 风格不存在: {STYLE_ID}")
        await close_mongodb()
        sys.exit(1)

    name = doc.get("name") or "上美画风"
    render_class = doc.get("render_class") or "illustration_2d"
    tags = doc.get("genre_tags") or []
    md = get_style_description_md(STYLE_ID, name, render_class, tags)
    if not md:
        print("[!] catalog 无 Markdown 内容")
        await close_mongodb()
        sys.exit(1)

    updated = await svc.update(STYLE_ID, {"style_description_md": md})
    if not updated:
        print("[!] update 失败")
        await close_mongodb()
        sys.exit(1)

    try:
        published = await svc.publish(STYLE_ID)
        status = "published"
    except ValueError as e:
        published = updated
        status = f"updated_draft ({e})"

    mp = published.get("model_prompts") or {}
    print(f"[ok] {STYLE_ID} · {name}")
    print(f"     status={status}")
    print(f"     md_len={len(md)}")
    print(f"     style_summary_zh={ (mp.get('style_summary_zh') or '')[:80] }…")
    print(f"     image_positive_en={ (mp.get('image_positive_en') or '')[:120] }…")
    print(f"     character_suffix_en={ (mp.get('character_suffix_en') or '')[:100] }…")
    await close_mongodb()


if __name__ == "__main__":
    asyncio.run(main())
