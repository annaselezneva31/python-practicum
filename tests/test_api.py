import json
from uuid import uuid4

import sqlalchemy


async def test_get_latest_fact_returns_404_when_empty(api_client):
    response = await api_client.get("/api/v1/facts/latest")
    assert response.status_code == 404


async def test_get_latest_fact_from_db(api_client, added_fact):
    response = await api_client.get("/api/v1/facts/latest")
    fact = response.json()
    assert fact["id"]
    assert fact["text"] == "New fact:Cats"
    assert fact["source"] == "http://cats.com"
    assert fact["created_at"]


async def test_get_latest_fact_from_cache(api_client, mock_redis_client):
    fake_redis_value = {
        "id": str(uuid4()),
        "text": "New fact:Dogs",
        "source": "http://dogs.com",
        "created_at": "2024-01-01T00:00:00",
    }
    await mock_redis_client.setex("latest_fact", 20, json.dumps(fake_redis_value))
    response = await api_client.get("/api/v1/facts/latest")
    fact = response.json()
    assert fact["id"]
    assert fact["text"] == "New fact:Dogs"
    assert fact["source"] == "http://dogs.com"
    assert fact["created_at"]


async def test_get_recent_facts_from_db(api_client, added_several_facts):
    response = await api_client.get("/api/v1/facts/", params={"limit": 4, "offset": 0})
    facts = response.json()
    assert facts["count"] == 3
    assert facts["items"][0]["id"]
    assert facts["items"][0]["text"] == "New fact_1:Cats"
    assert facts["items"][0]["source"] == "http://cats_1.com"
    assert facts["items"][0]["created_at"]


async def test_get_limit_2_recent_facts_from_db(api_client, added_several_facts):
    response = await api_client.get("/api/v1/facts/", params={"limit": 2, "offset": 0})
    facts = response.json()
    assert facts["count"] == 2
    assert facts["items"][0]["id"]
    assert facts["items"][0]["text"] == "New fact_1:Cats"
    assert facts["items"][0]["source"] == "http://cats_1.com"
    assert facts["items"][0]["created_at"]


async def test_get_offset_2_recent_facts_from_db(api_client, added_several_facts):
    response = await api_client.get("/api/v1/facts/", params={"limit": 2, "offset": 2})
    facts = response.json()
    assert facts["count"] == 1
    assert facts["items"][0]["id"]
    assert facts["items"][0]["text"] == "New fact_3:Cats"
    assert facts["items"][0]["source"] == "http://cats_3.com"
    assert facts["items"][0]["created_at"]


async def test_get_offset_4_recent_facts_from_db(api_client, added_several_facts):
    response = await api_client.get("/api/v1/facts/", params={"limit": 2, "offset": 4})
    facts = response.json()
    assert facts["count"] == 0
    assert facts["items"] == []


async def test_get_recent_facts_from_empty_db(api_client, db_tables):
    response = await api_client.get("/api/v1/facts/", params={"limit": 3, "offset": 0})
    facts = response.json()
    assert facts["count"] == 0
    assert facts["items"] == []


async def test_get_facts_invalid_limit(api_client, added_fact):
    response = await api_client.get("/api/v1/facts/", params={"limit": 0})
    assert response.status_code == 422


async def test_cache_populated_after_db_miss(
    api_client, added_fact, mock_redis_client, db_container
):
    # cache is empty
    cache_empty = await mock_redis_client.get("latest_fact")
    assert cache_empty is None

    # Get fact from DB and consequently fact is added to cache
    response_from_db = await api_client.get("/api/v1/facts/latest")
    fact_from_db = response_from_db.json()
    assert response_from_db.status_code == 200
    assert fact_from_db["text"] == "New fact:Cats"

    # cache is populated
    cache_empty = await mock_redis_client.get("latest_fact")
    assert cache_empty is not None

    # delete fact from DB
    url = db_container.get_connection_url()  # psycopg2 url, fine for DDL
    engine = sqlalchemy.create_engine(url)
    with engine.begin() as conn:
        conn.execute(sqlalchemy.text("DELETE FROM facts"))

    # Get fact from api from Redis
    response_from_cache = await api_client.get("/api/v1/facts/latest")
    fact_from_cache = response_from_cache.json()
    assert fact_from_cache == fact_from_db
