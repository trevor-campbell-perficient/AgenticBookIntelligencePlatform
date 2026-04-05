import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys

# Mock httpx if not installed
try:
    import httpx
except ImportError:
    httpx = MagicMock()
    sys.modules['httpx'] = httpx

@pytest.mark.asyncio
async def test_search_books_returns_results():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "search": {
                "results": [
                    {"id": 1, "title": "Dune", "author_names": ["Frank Herbert"]}
                ]
            }
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        from mcp_servers.books.hardcover_client import HardcoverClient
        client = HardcoverClient(api_key="test_key")
        results = await client.search_books("Dune")

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["title"] == "Dune"

@pytest.mark.asyncio
async def test_search_books_returns_structured_error_on_timeout():
    import httpx as _httpx

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=_httpx.TimeoutException("timeout"))
        mock_client_class.return_value = mock_client

        from importlib import reload
        import mcp_servers.books.hardcover_client as m
        reload(m)
        client = m.HardcoverClient(api_key="test_key")
        result = await client.search_books("Dune")

    assert result["error"] is True
    assert result["errorCategory"] == "transient"
    assert result["isRetryable"] is True

@pytest.mark.asyncio
async def test_get_book_details_returns_not_found_error():
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {"books": []}}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        from importlib import reload
        import mcp_servers.books.hardcover_client as m
        reload(m)
        client = m.HardcoverClient(api_key="test_key")
        result = await client.get_book_details(99999)

    assert result["error"] is True
    assert result["errorCategory"] == "validation"
    assert result["isRetryable"] is False
