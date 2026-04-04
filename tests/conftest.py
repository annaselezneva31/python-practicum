import pytest
import pytest_asyncio
import sqlalchemy
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from unittest.mock import patch
import redis.asyncio as redis
import redis as sync_redis

from app.core.config import Settings
from app.main import app
from app.db.models import Base, Fact
import app.db.session as session_module
import app.services.cache as cache_module


# ── Containers (session scope, sync — testcontainers are sync) ────────────────
@pytest.fixture(scope="session")
def db_container():
    with PostgresContainer("postgres:16") as container:
        yield container

@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer() as container:
        yield container

# ── Engine creation (session scope, sync engine) ─────────────────
@pytest.fixture(scope="session")
def sync_db_engine(db_container):
    url = db_container.get_connection_url()  # psycopg2 url, fine for DDL
    engine = sqlalchemy.create_engine(url)
    yield engine
    engine.dispose()

# ── Schema creation (session scope, sync engine) ─────────────────
@pytest.fixture(scope="session")
def db_tables(sync_db_engine):
    Base.metadata.create_all(sync_db_engine)
    yield
    Base.metadata.drop_all(sync_db_engine)


# ── Sync Redis client (session scope) ─────────────────────────────────────────
@pytest.fixture(scope="session")
def sync_redis_client(redis_container):
    redis_host = redis_container.get_container_host_ip()
    redis_port = redis_container.get_exposed_port(6379)
    redis_client_sync = sync_redis.Redis(host=redis_host, port=redis_port)
    yield redis_client_sync
    redis_client_sync.close()

# ── Settings override (session scope) ─────────────────────────────────────────
@pytest.fixture(scope="session")
def test_settings(db_container, redis_container):
    db_host = db_container.get_container_host_ip()
    db_port = db_container.get_exposed_port(5432)

    # Get actual credentials from the container
    db_user = db_container.username
    db_password = db_container.password
    db_name = db_container.dbname

    async_db_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    redis_host = redis_container.get_container_host_ip()
    redis_port = redis_container.get_exposed_port(6379)
    redis_url = f"redis://{redis_host}:{redis_port}"

    return Settings(
        database_url=async_db_url,
        redis_url=redis_url,
    )

@pytest.fixture(scope="session")
def override_settings(test_settings):
    # Patch get_settings everywhere it is called directly
    with patch("app.core.config.get_settings", return_value=test_settings), \
         patch("app.db.session.get_settings", return_value=test_settings), \
         patch("app.services.cache.get_settings", return_value=test_settings), \
         patch("app.main.get_settings", return_value=test_settings):
        # Reset lazy singletons so they reinitialize with patched settings
        session_module._engine = None
        session_module._AsyncSessionMaker = None
        cache_module._redis_client = None

        yield

    # Cleanup after session
    session_module._engine = None
    session_module._AsyncSessionMaker = None
    cache_module._redis_client = None


# ── Async HTTP client (session scope) ─────────────────────────────────────────
@pytest.fixture(scope="session")
async def api_client(override_settings, db_tables):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost",
    ) as client:
        yield client


# ── Table truncation between tests (function scope) ───────────────────────────
@pytest.fixture(autouse=True)
def truncate_tables(sync_db_engine, db_tables, override_settings, sync_redis_client):
    """Runs after every test to reset DB state."""
    yield
    # url = db_container.get_connection_url()  # psycopg2 url, fine for DDL
    # engine = sqlalchemy.create_engine(url)
    with sync_db_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete()) # deletes all tables
    sync_redis_client.flushall() # clears all data from cache


# ── Creating Test data (function scope) ───────────────────────────
@pytest.fixture(scope="function")
def added_fact(override_settings, sync_db_engine, db_tables):
    with Session(sync_db_engine, expire_on_commit=False) as session:
        fact = Fact(text='New fact:Cats', source='http://cats.com')
        session.add(fact)
        session.commit()
        yield fact

@pytest.fixture(scope="function")
def mock_redis_client(redis_container):
    redis_host = redis_container.get_container_host_ip()
    redis_port = redis_container.get_exposed_port(6379)
    redis_url = f"redis://{redis_host}:{redis_port}"
    redis_client = redis.from_url(redis_url, decode_responses=True)
    yield redis_client
    redis_client.close()

@pytest.fixture(scope="function")
def added_several_facts(override_settings, sync_db_engine, db_tables):
    with Session(sync_db_engine, expire_on_commit=False) as session:
        facts = []
        for i in range(3):
            fact = Fact(text=f'New fact_{i + 1}:Cats', source=f'http://cats_{i + 1}.com')
            facts.append(fact)
        session.add_all(facts)
        session.commit()
        yield facts