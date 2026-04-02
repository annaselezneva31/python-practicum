import json
from typing import Any

import redis.asyncio as redis
from app.core.config import get_settings
from app.db.models import Fact
from app.schemas.fact import FactResponse


settings = get_settings()
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

async def get_latest_fact() -> dict | None:
    try:
        latest_fact = await redis_client.get("latest_fact")
        if not latest_fact:
            return None

        return json.loads(latest_fact)  # conver string to Python dict
    except Exception as e:
        print(f"Redis error {e}")
        return None

async def set_latest_fact(fact: Fact) -> None:
    fact_json = FactResponse.model_validate(fact).model_dump_json()
    try:
        await redis_client.setex("latest_fact",
                                 settings.fetch_interval_seconds,
                                 fact_json
                                 )
    except Exception as e:
        print(f"Redis error {e}")


def close_redis():
    ...