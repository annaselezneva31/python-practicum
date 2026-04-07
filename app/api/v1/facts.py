from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import FactRepository, get_fact_repository
from app.db.session import get_session
from app.schemas.fact import FactListResponse, FactResponse
from app.services.cache import get_latest_fact, set_latest_fact

router = APIRouter()


@router.get("/latest")
async def get_latest_fact_endpoint(
    session: AsyncSession = Depends(get_session),
    repo: FactRepository = Depends(get_fact_repository),
) -> FactResponse:
    # look up latest fact in Redis
    cached_fact = await get_latest_fact()
    if cached_fact:
        return FactResponse(**cached_fact)

    fact = await repo.get_latest()
    if not fact:
        raise HTTPException(status_code=404, detail="No facts available")

    await set_latest_fact(fact)  # add latest fact to Redis
    return FactResponse(
        id=fact.id,
        text=fact.text,
        source=fact.source,
        created_at=fact.created_at,
    )


@router.get("/")
async def get_recent_facts(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    repo: FactRepository = Depends(get_fact_repository),
) -> FactListResponse:
    facts = await repo.get_recent(limit=limit, offset=offset)
    items = [
        FactResponse(
            id=f.id,
            text=f.text,
            source=f.source,
            created_at=f.created_at,
        )
        for f in facts
    ]
    return FactListResponse(count=len(items), items=items)
