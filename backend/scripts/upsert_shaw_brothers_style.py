"""创建/更新「邵氏风格」preset，写入详细 style_description_md 并发布。"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import close_mongodb, init_mongodb
from app.core.drama.style_description_catalog import get_style_description_md
from app.services.drama_style_service import get_drama_style_service

STYLE_ID = "shaw_brothers_cinema"
STYLE_FIELDS = {
    "style_id": STYLE_ID,
    "name": "邵氏风格",
    "render_class": "live_action",
    "genre_tags": ["邵氏", "港片", "武侠", "古装", "片厂"],
    "origin": "seed",
}


async def main() -> None:
    await init_mongodb()
    svc = get_drama_style_service()
    existing = await svc.get_by_style_id(STYLE_ID)

    md = get_style_description_md(
        STYLE_ID,
        STYLE_FIELDS["name"],
        STYLE_FIELDS["render_class"],
        STYLE_FIELDS["genre_tags"],
    )
    if not md:
        print("[!] STYLE_PROFILES 无 Markdown 内容")
        await close_mongodb()
        sys.exit(1)

    payload = {**STYLE_FIELDS, "style_description_md": md}

    if existing:
        updated = await svc.update(STYLE_ID, payload)
        action = "updated"
    else:
        updated = await svc.create({**payload, "publish": False})
        action = "created"

    if not updated:
        print(f"[!] {action} 失败")
        await close_mongodb()
        sys.exit(1)

    try:
        published = await svc.publish(STYLE_ID)
        status = published.get("status") if published else "failed"
    except ValueError as e:
        status = f"draft ({e})"
        published = updated

    mp = (published or {}).get("model_prompts") or {}
    print(f"[ok] {action} · {STYLE_ID} · {STYLE_FIELDS['name']}")
    print(f"     status={status}")
    print(f"     md_len={len(md)}")
    print(f"     style_summary_zh={(mp.get('style_summary_zh') or '')[:120]}…")
    print(f"     image_positive_en={(mp.get('image_positive_en') or '')[:140]}…")
    await close_mongodb()


if __name__ == "__main__":
    asyncio.run(main())
