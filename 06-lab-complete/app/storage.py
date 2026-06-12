"""Redis-backed state with a small local fallback for direct development."""
import json
import logging
from collections import defaultdict, deque
from typing import Any

import redis

from app.config import settings

logger = logging.getLogger(__name__)
_client: redis.Redis | None = None
_local_history: dict[str, deque[dict[str, Any]]] = defaultdict(deque)


def redis_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
    return _client


def redis_available() -> bool:
    try:
        return bool(redis_client().ping())
    except redis.RedisError:
        return False


def get_history(user_id: str) -> list[dict[str, Any]]:
    key = f"conversation:{user_id}"
    try:
        values = redis_client().lrange(key, -settings.conversation_max_messages, -1)
        return [json.loads(value) for value in values]
    except redis.RedisError:
        return list(_local_history[user_id])


def append_history(user_id: str, message: dict[str, Any]) -> None:
    key = f"conversation:{user_id}"
    payload = json.dumps(message, ensure_ascii=False)
    try:
        client = redis_client()
        pipeline = client.pipeline()
        pipeline.rpush(key, payload)
        pipeline.ltrim(key, -settings.conversation_max_messages, -1)
        pipeline.expire(key, settings.conversation_ttl_seconds)
        pipeline.execute()
    except redis.RedisError:
        history = _local_history[user_id]
        history.append(message)
        while len(history) > settings.conversation_max_messages:
            history.popleft()


def close_storage() -> None:
    global _client
    if _client is not None:
        try:
            _client.close()
        finally:
            _client = None
