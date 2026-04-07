from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.repository import FactRepository
from app.db.session import get_engine

TEXT = "New fact: rabbit"
SOURCE = "hhtp://rabbit.com"


@asynccontextmanager
async def make_repo():
    _, async_session_maker = get_engine()
    async with async_session_maker() as session:
        yield FactRepository(session)


async def test_create_fact():

    async with make_repo() as repo:
        res = await repo.create(text=TEXT, source=SOURCE)
        assert res.id
        assert res.text == TEXT
        assert res.source == SOURCE
        assert res.created_at


async def test_create_fact_duplicate_raises_error():
    async with make_repo() as repo:
        await repo.create(text=TEXT, source=SOURCE)
        with pytest.raises(IntegrityError):
            await repo.create(text=TEXT, source=SOURCE)


async def test_get_latest_fact():
    async with make_repo() as repo:
        await repo.create(text=TEXT, source=SOURCE)
        res = await repo.get_latest()
        assert res.id
        assert res.text == TEXT
        assert res.source == SOURCE
        assert res.created_at


async def test_get_latest_fact_several_facts():
    async with make_repo() as repo:
        uuid_1 = uuid4()
        uuid_2 = uuid4()

        await repo.create(id=uuid_1, text=TEXT, source=SOURCE)
        await repo.create(id=uuid_2, text=TEXT + "1", source=SOURCE + "1")

        res = await repo.get_latest()
        assert res.id == uuid_2


async def test_get_latest_fact_db_empty():
    async with make_repo() as repo:
        res = await repo.get_latest()
        assert res is None


async def test_get_recent_facts():
    async with make_repo() as repo:
        await repo.create(text=TEXT, source=SOURCE)
        await repo.create(text=TEXT + "1", source=SOURCE + "1")
        await repo.create(text=TEXT + "2", source=SOURCE + "2")
        res = await repo.get_recent()
        assert len(res) == 3
        assert res[2].id
        assert res[2].text == TEXT
        assert res[2].source == SOURCE
        assert res[2].created_at


async def test_get_recent_facts_db_empty():
    async with make_repo() as repo:
        res = await repo.get_recent()
        assert len(res) == 0


async def test_get_recent_facts_limit_2():
    async with make_repo() as repo:
        await repo.create(text=TEXT, source=SOURCE)
        await repo.create(text=TEXT + "1", source=SOURCE + "1")
        await repo.create(text=TEXT + "2", source=SOURCE + "2")
        res = await repo.get_recent(limit=2)
        assert len(res) == 2
        assert res[1].id
        assert res[1].text == TEXT + "1"
        assert res[1].source == SOURCE + "1"
        assert res[1].created_at


async def test_get_recent_facts_offset_2():
    async with make_repo() as repo:
        await repo.create(text=TEXT, source=SOURCE)
        await repo.create(text=TEXT + "1", source=SOURCE + "1")
        await repo.create(text=TEXT + "2", source=SOURCE + "2")
        res = await repo.get_recent(offset=2)
        assert len(res) == 1
        assert res[0].id
        assert res[0].text == TEXT
        assert res[0].source == SOURCE
        assert res[0].created_at


async def test_get_recent_facts_offset_4():
    async with make_repo() as repo:
        await repo.create(text=TEXT, source=SOURCE)
        await repo.create(text=TEXT + "1", source=SOURCE + "1")
        await repo.create(text=TEXT + "2", source=SOURCE + "2")
        res = await repo.get_recent(offset=4)
        assert len(res) == 0
