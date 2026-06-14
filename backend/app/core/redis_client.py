import redis.asyncio as redis
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger()

_redis_client: redis.Redis = None


async def init_redis() -> None:
    global _redis_client
    try:
        _redis_client = redis.from_url(settings.redis_url)
        await _redis_client.ping()
        logger.info("Redis连接成功")
    except Exception as e:
        logger.error(f"Redis连接失败: {e}")
        raise


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        logger.info("Redis连接已关闭")


def get_redis() -> redis.Redis:
    return _redis_client
