"""Per-user monthly cost protection backed by Redis."""
from datetime import datetime, timezone

import redis
from fastapi import HTTPException

from app.config import settings
from app.storage import redis_client


_local_spend: dict[str, float] = {}


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006


def check_and_record_cost(user_id: str, input_tokens: int, output_tokens: int) -> float:
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    key = f"budget:{user_id}:{month}"
    cost = estimate_cost(input_tokens, output_tokens)
    try:
        client = redis_client()
        current = float(client.get(key) or 0)
        if current + cost > settings.monthly_budget_usd:
            raise HTTPException(402, "Monthly agent budget exceeded")
        new_total = float(client.incrbyfloat(key, cost))
        client.expire(key, 32 * 24 * 3600)
        return new_total
    except redis.RedisError:
        current = _local_spend.get(key, 0.0)
        if current + cost > settings.monthly_budget_usd:
            raise HTTPException(402, "Monthly agent budget exceeded")
        _local_spend[key] = current + cost
        return _local_spend[key]


def get_monthly_spend(user_id: str) -> float:
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    key = f"budget:{user_id}:{month}"
    try:
        return float(redis_client().get(key) or 0)
    except redis.RedisError:
        return _local_spend.get(key, 0.0)
