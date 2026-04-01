from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Fact
from app.db.session import get_session


class FactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, text: str, source: str, id: UUID | None = None) -> Fact:
        fact = (
            Fact(id=id, text=text, source=source)
            if id
            else Fact(text=text, source=source)
        )
        self.session.add(fact)
        await self.session.commit()
        await self.session.refresh(fact)
        return fact

    async def get_latest(self) -> Fact | None:
        result = await self.session.execute(
            select(Fact).order_by(Fact.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_recent(self, limit: int = 10, offset: int = 0) -> list[Fact]:
        result = await self.session.execute(
            select(Fact).order_by(Fact.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, fact_id: int) -> Fact | None:
        result = await self.session.execute(select(Fact).where(Fact.id == fact_id))
        return result.scalar_one_or_none()


async def get_fact_repository(
    session: AsyncSession = Depends(get_session),
) -> AsyncIterator[FactRepository]:
    yield FactRepository(session)
