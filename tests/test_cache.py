from datetime import datetime, timezone
from unittest.mock import ANY, AsyncMock, patch
from uuid import uuid4

from app.core.config import get_settings
from app.db.models import Fact
from app.services.cache import get_latest_fact, set_latest_fact

settings = get_settings()


async def test_get_latest_fact_returns_dict():
    fake_redis_value = '{"id": "123", "text": "fun fact", "source": "http://...", "created_at": "2024-01-01T00:00:00"}'
    mock_redis = AsyncMock()
    mock_redis.get.return_value = fake_redis_value
    with patch("app.services.cache.get_redis_client", return_value=mock_redis):
        result = await get_latest_fact()
        assert isinstance(result, dict)
        assert result["id"] == "123"


async def test_get_latest_fact_returns_none():
    fake_redis_value = None
    mock_redis = AsyncMock()
    mock_redis.get.return_value = fake_redis_value
    with patch("app.services.cache.get_redis_client", return_value=mock_redis):
        result = await get_latest_fact()
        assert result is None


async def test_get_latest_fact_returns_none_on_redis_error():
    mock_redis = AsyncMock()
    mock_redis.get.side_effect = Exception("Redis down")
    with patch("app.services.cache.get_redis_client", return_value=mock_redis):
        result = await get_latest_fact()
        print(result)
        assert result is None


async def test_set_latest_fact_called_with_correct_args():
    fake_fact = Fact(
        id=uuid4(),
        text="fun fact",
        source="http://...",
        created_at=datetime.now(timezone.utc),
    )
    mock_redis = AsyncMock()
    with patch("app.services.cache.get_redis_client", return_value=mock_redis):
        await set_latest_fact(fake_fact)
        mock_redis.setex.assert_called_once_with(
            "latest_fact",  # correct key
            settings.fetch_interval_seconds,  # correct TTL
            ANY,  # don't care about exact JSON value
        )
