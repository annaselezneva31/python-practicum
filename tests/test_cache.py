from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, ANY
import pytest
from uuid import uuid4

from app.services.cache import get_latest_fact, set_latest_fact
from app.db.models import Fact
from app.core.config import get_settings

settings = get_settings()

@pytest.mark.asyncio
async def test_get_latest_fact_returns_dict():
    fake_redis_value = '{"id": "123", "text": "fun fact", "source": "http://...", "created_at": "2024-01-01T00:00:00"}'
    with patch("app.services.cache.redis_client.get",
               new=AsyncMock(return_value=fake_redis_value)):
        result = await get_latest_fact()
        assert isinstance(result, dict)
        assert result['id'] == "123"

@pytest.mark.asyncio
async def test_get_latest_fact_returns_none():
    fake_redis_value = None
    with patch("app.services.cache.redis_client.get",
               new=AsyncMock(return_value=fake_redis_value)):
        result = await get_latest_fact()
        assert result is None

@pytest.mark.asyncio
async def test_get_latest_fact_returns_none_on_redis_error():
    mock_redis = AsyncMock(side_effect=Exception("Redis down"))
    with patch("app.services.cache.redis_client.get",
               new=mock_redis):
        result = await get_latest_fact()
        assert result is None

@pytest.mark.asyncio
async def test_set_latest_fact_called_with_correct_args():
    fake_fact = Fact(id=uuid4(), text="fun fact", source="http://...", created_at=datetime.now(timezone.utc))
    mock_setex = AsyncMock()
    with patch("app.services.cache.redis_client.setex", new=mock_setex):
        await set_latest_fact(fake_fact)
        mock_setex.assert_called_once_with(
            "latest_fact",  # correct key
            settings.fetch_interval_seconds,  # correct TTL
            ANY  # don't care about exact JSON value
        )