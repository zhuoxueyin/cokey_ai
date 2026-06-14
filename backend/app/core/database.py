from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger()

_mongodb_client: AsyncIOMotorClient = None
_mongodb_db: AsyncIOMotorDatabase = None


async def init_mongodb() -> None:
    global _mongodb_client, _mongodb_db
    try:
        _mongodb_client = AsyncIOMotorClient(settings.mongodb_url)
        _mongodb_db = _mongodb_client[settings.mongodb_db_name]
        await _mongodb_db.command("ping")
        logger.info(f"MongoDB连接成功: {settings.mongodb_db_name}")
    except Exception as e:
        logger.error(f"MongoDB连接失败: {e}")
        raise


async def close_mongodb() -> None:
    global _mongodb_client
    if _mongodb_client:
        _mongodb_client.close()
        logger.info("MongoDB连接已关闭")


def get_db() -> AsyncIOMotorDatabase:
    return _mongodb_db


def get_collection(name: str):
    return _mongodb_db[name]
