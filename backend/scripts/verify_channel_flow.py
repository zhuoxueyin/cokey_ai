"""端到端验证：渠道配置能否被网关正确读取（明文 API Key）"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_mongodb
from app.services.channel_service import get_channel_service
from app.services.model_service import get_model_service
from app.adapters import create_adapter
from app.core.utils import generate_trace_id


async def main():
    await init_mongodb()
    channel_svc = get_channel_service()
    model_svc = get_model_service()
    trace_id = generate_trace_id()

    print("=" * 70)
    print("Test 1: 读取所有渠道配置（明文 auth_config）")
    print("=" * 70)

    channels = ["weelink_text", "weelink_image", "weelink_video", "weelink_text_default"]
    for code in channels:
        channel = await channel_svc.get_by_code(code)
        if not channel:
            print(f"  [FAIL] {code}: 渠道不存在")
            continue
        ac = channel.get("auth_config", {})
        print(f"\n  [{code}] {channel.get('channel_name')}")
        for k, v in ac.items():
            if v and isinstance(v, str) and len(v) > 12:
                print(f"    - {k}: ...{v[-8:]} (len={len(v)})")
            else:
                print(f"    - {k}: {v!r}")
        print(f"    -> status={channel.get('status')}")

    print("\n" + "=" * 70)
    print("Test 2: 创建 adapter 并读取 API Key（模拟网关调用）")
    print("=" * 70)

    for code in channels:
        channel = await channel_svc.get_by_code(code)
        if not channel:
            continue
        adapter = create_adapter(channel, trace_id)
        if not adapter:
            print(f"  [FAIL] {code}: 无法创建 adapter")
            continue
        for category in ["text", "image", "video"]:
            api_key = adapter.get_api_key_for_category(category)
            status = "OK" if api_key else "(空/占位符)"
            snippet = f"...{api_key[-6:]}" if api_key else "-"
            print(f"  [{code}] category={category}: api_key={snippet} {status}")

    print("\n" + "=" * 70)
    print("Test 3: 检查几个已知模型的 channel_bindings")
    print("=" * 70)

    model_codes_to_check = ["gpt-4o", "gpt-5.5", "dall-e-3"]
    for mcode in model_codes_to_check:
        model = await model_svc.get_by_code(mcode)
        if not model:
            print(f"  Model {mcode}: 不存在")
            continue
        bindings = model.get("channel_bindings", [])
        print(f"  Model {mcode}: {len(bindings)} 个渠道绑定")
        for b in bindings:
            print(f"    - channel={b.get('channel_code')}, model_id={b.get('channel_model_id')}, priority={b.get('priority')}, status={b.get('status')}")

    print("\n" + "=" * 70)
    print("验证完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
