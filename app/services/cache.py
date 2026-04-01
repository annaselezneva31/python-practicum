import json
from typing import Any

import redis.asyncio as redis
from app.core.config import get_settings

settings = get_settings()

def close_redis():
    ...