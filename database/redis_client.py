# database/python/redis_client.py

"""
Redis Client Module

Is module ka kaam:
- settings (src/app/config.py) se Redis config read karna
- Redis client create karna
- get_redis_client() function export karna

Ye client:
- LangGraph checkpointer ke liye bhi use hoga
- Redis-based caching ke liye bhi
"""

import redis
from src.app.config import settings


def get_redis_client() -> redis.Redis:
    """
    Creates and returns a Redis client instance.

    This client will be used by:
    - LangGraph RedisCheckpointer
    - cache layer (optional)
    """
    client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,  # values ko string mein return karega
    )
    return client
