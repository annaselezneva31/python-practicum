from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.facts import router as facts_router
from app.core.config import get_settings
from app.db.models import Base
from app.db.session import get_engine
from app.services.cache import close_redis

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # create DB
    engine, _ = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await close_redis()


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


Instrumentator().instrument(app).expose(app)

app.include_router(facts_router, prefix="/api/v1/facts", tags=["facts"])
