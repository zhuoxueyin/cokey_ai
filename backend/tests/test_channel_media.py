"""渠道 base64 响应归一化测试"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.channel_media import enrich_parsed_result


async def test_enrich_image_b64():
    uploaded = []

    async def fake_upload(data: str, ext: str):
        uploaded.append((ext, len(data)))
        return f"https://cdn.example.com/out{ext}"

    parsed = {"type": "image_edits", "raw": {"data": [{"b64_json": "aGVsbG8="}]}}
    raw = {"data": [{"b64_json": "aGVsbG8=", "revised_prompt": "test"}]}
    out = await enrich_parsed_result(
        parsed, raw, "image", upload_b64=fake_upload, trace_id="t1"
    )
    assert out["type"] == "image"
    assert len(out["images"]) == 1
    assert out["images"][0]["url"].startswith("https://cdn.example.com")
    assert uploaded[0][0] == ".png"


async def test_enrich_video_b64():
    async def fake_upload(data: str, ext: str):
        return f"https://cdn.example.com/vid{ext}"

    parsed = {"type": "video", "videos": []}
    raw = {"data": [{"b64_json": "dmlkZW8=", "revised_prompt": ""}]}
    out = await enrich_parsed_result(
        parsed, raw, "video", upload_b64=fake_upload, trace_id="t2"
    )
    assert out["type"] == "video"
    assert len(out["videos"]) == 1
    assert "cdn.example.com" in out["videos"][0]["url"]


if __name__ == "__main__":
    asyncio.run(test_enrich_image_b64())
    asyncio.run(test_enrich_video_b64())
    print("channel_media tests passed")
