import asyncio
import time
import json
from typing import Any
from uuid import UUID

import httpx
from celery import current_task
import redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import inspect
from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.db.models import Fact
from app.db.session import settings as db_settings

settings = get_settings()


async def store_fact(
    fact_text: str, source: str, task_uuid: UUID | None = None
) -> dict[str, Any]:
    local_engine = create_async_engine(db_settings.database_url, future=True)
    LocalSession = async_sessionmaker(
        local_engine, expire_on_commit=False, autoflush=False
    )
    try:
        async with LocalSession() as session:
            fact = (
                Fact(id=task_uuid, text=fact_text, source=source)
                if task_uuid
                else Fact(text=fact_text, source=source)
            )
            session.add(fact)
            await session.commit()
            await session.refresh(fact)
            return {
                c.key: getattr(fact, c.key) for c in inspect(fact).mapper.column_attrs
            }
    finally:
        await local_engine.dispose()


@celery_app.task
def fetch_and_store_fact() -> dict[str, Any]:
    source_url = settings.external_fact_api
    try:
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            response = client.get(
                source_url,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

        fact_text = data.get("text", "")
        task_id_str = getattr(current_task.request, "id", None)
        try:
            task_uuid: UUID | None = UUID(task_id_str) if task_id_str else None
        except Exception:
            task_uuid = None

        saved_fact = asyncio.run(store_fact(fact_text, source_url, task_uuid))
        saved_fact["id"] = task_id_str
        saved_fact["created_at"] = str(saved_fact["created_at"])
        
        r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        r.setex(
            "latest_fact",
            settings.fetch_interval_seconds,
            json.dumps(saved_fact),
        )
        del saved_fact["id"]
        return {
            "status": "success",
            "task_id": task_id_str,
            **saved_fact,
        }
    except Exception as e:
        raise RuntimeError(f"fetch_and_store_fact failed: {e}") from e
