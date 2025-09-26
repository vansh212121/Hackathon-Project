import redis.asyncio as redis
from src.app.core.config import settings


redis_client = redis.from_url(
    f"{settings.REDIS_URL}", encoding="utf-8", decode_responses=True
)
