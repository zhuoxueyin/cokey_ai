"""
迁移脚本：将 Volcengine 渠道类型从 "volcengine" 改为 "direct"

执行方式：
    cd backend
    python scripts/migrate_volcengine_to_direct.py

说明：
- 该脚本会将所有 channel_type 为 "volcengine" 的渠道改为 "direct"
- 保留原有配置不变，仅修改渠道类型标识
- 适配器注册逻辑已兼容旧配置，但建议使用新类型以符合规范
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


async def migrate():
    """执行迁移"""
    print("=" * 60)
    print("Volcengine 渠道类型迁移脚本")
    print("=" * 60)
    
    # 连接 MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    # 查询所有 volcengine 类型的渠道
    channels = await db.channels.find(
        {"channel_type": "volcengine"}
    ).to_list(length=None)
    
    if not channels:
        print("\n✅ 未找到需要迁移的渠道（channel_type='volcengine'）")
        print("   所有 Volcengine 渠道已使用正确的类型标识")
        return
    
    print(f"\n📋 找到 {len(channels)} 个需要迁移的渠道：")
    for ch in channels:
        print(f"   - {ch['channel_code']} ({ch['channel_name']})")
    
    # 确认迁移
    confirm = input("\n⚠️  是否执行迁移？(yes/no): ").strip().lower()
    if confirm != "yes":
        print("\n❌ 已取消迁移")
        return
    
    # 执行更新
    result = await db.channels.update_many(
        {"channel_type": "volcengine"},
        {"$set": {"channel_type": "direct"}}
    )
    
    print(f"\n✅ 迁移完成！")
    print(f"   已更新 {result.modified_count} 个渠道")
    print(f"   channel_type: 'volcengine' → 'direct'")
    
    # 验证迁移结果
    remaining = await db.channels.count_documents({"channel_type": "volcengine"})
    if remaining == 0:
        print("\n✅ 验证通过：无遗留的 volcengine 类型渠道")
    else:
        print(f"\n⚠️  警告：仍有 {remaining} 个渠道未迁移")
    
    # 显示迁移后的渠道列表
    updated_channels = await db.channels.find(
        {"channel_code": {"$regex": "volcengine", "$options": "i"}}
    ).to_list(length=None)
    
    if updated_channels:
        print("\n📊 迁移后的 Volcengine 渠道列表：")
        for ch in updated_channels:
            print(f"   - {ch['channel_code']}: type={ch['channel_type']}, status={ch['status']}")
    
    print("\n" + "=" * 60)
    print("提示：建议重启后端服务使变更生效")
    print("      python launcher.py restart")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(migrate())
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
