"""将宫斗权谋冷峻、复古科幻原子朋克详细风格描述写入 MongoDB 并发布。"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import close_mongodb, init_mongodb
from app.core.drama.style_description_catalog import get_style_description_md
from app.services.drama_style_service import get_drama_style_service

TARGET_STYLE_IDS = (
    "palace_intrigue_cold",
    "retro_sci_fi_atompunk",
)


async def upsert_one(svc, style_id: str) -> dict:
    doc = await svc.get_by_style_id(style_id)
    if not doc:
        return {"style_id": style_id, "action": "not_found"}

    name = doc.get("name") or style_id
    render_class = doc.get("render_class") or "live_action"
    tags = doc.get("genre_tags") or []
    md = get_style_description_md(style_id, name, render_class, tags)
    if not md:
        return {"style_id": style_id, "name": name, "action": "missing_md"}

    updated = await svc.update(style_id, {"style_description_md": md})
    if not updated:
        return {"style_id": style_id, "name": name, "action": "update_failed"}

    try:
        published = await svc.publish(style_id)
        status = "published"
    except ValueError as e:
        published = updated
        status = f"updated_draft ({e})"

    mp = published.get("model_prompts") or {}
    return {
        "style_id": style_id,
        "name": name,
        "action": "updated",
        "status": status,
        "md_len": len(md),
        "summary_preview": (mp.get("style_summary_zh") or "")[:100],
        "image_prompt_preview": (mp.get("image_positive_en") or "")[:120],
    }


async def main() -> None:
    await init_mongodb()
    svc = get_drama_style_service()
    for style_id in TARGET_STYLE_IDS:
        result = await upsert_one(svc, style_id)
        action = result.get("action")
        if action == "updated":
            print(f"[ok] {result['style_id']} · {result['name']}")
            print(f"     status={result['status']}")
            print(f"     md_len={result['md_len']}")
            print(f"     summary={result['summary_preview']}…")
            print(f"     image={result['image_prompt_preview']}…")
        else:
            print(f"[!] {style_id} · {action}")
    await close_mongodb()


if __name__ == "__main__":
    asyncio.run(main())
