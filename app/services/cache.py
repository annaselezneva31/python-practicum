import json
import redis.asyncio as redis
from app.core.config import get_settings
from app.db.models import Fact
from app.schemas.fact import FactResponse


_redis_client = None

def get_redis_client():
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client

async def get_latest_fact() -> dict | None:
    redis_client = get_redis_client()
    try:
        latest_fact = await redis_client.get("latest_fact")
        if not latest_fact:
            return None
        return json.loads(latest_fact)
    except Exception as e:
        print(f"Redis error {e}")
        return None

async def set_latest_fact(fact: Fact) -> None:
    settings = get_settings()
    redis_client = get_redis_client()
    fact_json = FactResponse.model_validate(fact).model_dump_json()
    try:
        await redis_client.setex("latest_fact", settings.fetch_interval_seconds, fact_json)
    except Exception as e:
        print(f"Redis error {e}")

async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None