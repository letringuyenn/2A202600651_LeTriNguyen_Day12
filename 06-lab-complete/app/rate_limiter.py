"""Per-user sliding-window rate limiting backed by Redis."""
import time
from collections import defaultdict, deque

import redis
from fastapi import HTTPException

from app.config import settings
from app.storage import redis_client

_local_windows: dict[str, deque[float]] = defaultdict(deque)


def _check_local(user_id: str, now: float) -> None:
    window = _local_windows[user_id]
    while window and window[0] <= now - 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(429, "Rate limit exceeded", headers={"Retry-After": "60"})
    window.append(now)


def check_rate_limit(user_id: str) -> None:
    now = time.time()
    key = f"rate:{user_id}"
    try:
        client = redis_client()
        pipeline = client.pipeline()
        pipeline.zremrangebyscore(key, 0, now - 60)
        pipeline.zcard(key)
        _, count = pipeline.execute()
        if count >= settings.rate_limit_per_minute:
            raise HTTPException(429, "Rate limit exceeded", headers={"Retry-After": "60"})
        member = f"{now:.6f}"
        pipeline = client.pipeline()
        pipeline.zadd(key, {member: now})
        pipeline.expire(key, 60)
        pipeline.execute()
    except redis.RedisError:
        _check_local(user_id, now)
