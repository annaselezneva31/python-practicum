import asyncio
import json
from typing import Any
from uuid import UUID

import httpx
import redis
from celery import current_task
from sqlalchemy import NullPool
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.db.models import Fact
from app.schemas.fact import FactResponse

settings = get_settings()
redis_client_sync = redis.Redis.from_url(settings.redis_url, decode_responses=True)


async def store_fact(fact_text: str, source: str, task_uuid: UUID | None = None) -> str:
    engine_db = create_async_engine(settings.database_url, poolclass=NullPool)
    async_session = async_sessionmaker(engine_db, expire_on_commit=False)
    async with async_session() as session:
        fact = (
            Fact(id=task_uuid, text=fact_text, source=source)
            if task_uuid
            else Fact(text=fact_text, source=source)
        )
        try:
            session.add(fact)
            await session.commit()
            await session.refresh(fact)
            return FactResponse.model_validate(fact).model_dump_json()
        except IntegrityError as e:
            # fact already exists - return existing one
            print(f"{e}")
            await session.rollback()
            existing_fact = await session.get(Fact, task_uuid)
            return FactResponse.model_validate(existing_fact).model_dump_json()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def fetch_and_store_fact(self) -> dict[str, Any]:
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

        # running async DB request inside sync Celery task
        saved_fact = asyncio.run(store_fact(fact_text, source_url, task_uuid))

        redis_client_sync.setex(
            "latest_fact",
            settings.fetch_interval_seconds,
            saved_fact,
        )
        return {
            "status": "success",
            "task_id": task_id_str,
            **json.loads(saved_fact),
        }
    except httpx.RequestError as e:
        raise self.retry(exc=e)
    except Exception as e:
        raise RuntimeError(f"fetch_and_store_fact failed: {e}") from e
