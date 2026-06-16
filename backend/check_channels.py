import asyncio
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient

async def check_channels():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]
    
    channels = db.channels.find()
    async for ch in channels:
        print(f"渠道: {ch['channel_code']}")
        print(f"  类型: {ch['channel_type']}")
        print(f"  auth_config: {ch.get('auth_config', {})}")
        print()

if __name__ == "__main__":
    asyncio.run(check_channels())
