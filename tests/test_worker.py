from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from app.tasks.facts import fetch_and_store_fact


def test_fetch_and_store_fact_success():
    mock_response = Mock()
    mock_response.json.return_value = {"text": "New fact"}
    mock_response.raise_for_status.return_value = None

    mock_client = Mock()
    mock_client.get.return_value = mock_response

    mock_redis = AsyncMock()
    mock_redis.setex.return_value = None

    mock_store_fact = '{"id": "123", "text": "New fact", "source": "http://", "created_at": "2024-01-01"}'

    with (
        patch("app.tasks.facts.httpx.Client") as mock_client_class,
        patch(
            "app.tasks.facts.store_fact", new=AsyncMock(return_value=mock_store_fact)
        ),
        patch("app.tasks.facts.redis_client_sync.setex", return_value=mock_redis),
    ):
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client_class.return_value.__exit__.return_value = None

        result = fetch_and_store_fact()
        assert result["status"] == "success"
        assert result["task_id"] is None
        assert result["id"]
        assert result["text"] == "New fact"
        assert result["source"]


def test_fetch_and_store_fact_retries_on_http_error():
    mock_client = Mock()
    mock_client.get.side_effect = httpx.RequestError("connection failed")

    with patch("app.tasks.facts.httpx.Client") as mock_client_class:
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client_class.return_value.__exit__.return_value = None

        with pytest.raises(httpx.RequestError):
            fetch_and_store_fact()


def test_fetch_and_store_fact_unexpected_error():
    mock_client = Mock()
    mock_client.get.side_effect = Exception("something bad happend")

    with patch("app.tasks.facts.httpx.Client") as mock_client_class:
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client_class.return_value.__exit__.return_value = None

        with pytest.raises(Exception):
            fetch_and_store_fact()
