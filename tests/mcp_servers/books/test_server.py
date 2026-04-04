import pytest
import sys
import json
from unittest.mock import AsyncMock, patch, MagicMock

# Mock mcp if not installed
if 'mcp' not in sys.modules:
    mcp_mock = MagicMock()
    sys.modules['mcp'] = mcp_mock
    sys.modules['mcp.server'] = mcp_mock
    sys.modules['mcp.server.stdio'] = mcp_mock
    sys.modules['mcp.types'] = mcp_mock

@pytest.mark.asyncio
async def test_handle_search_books_returns_list():
    mock_client = AsyncMock()
    mock_client.search_books.return_value = [{"id": "1", "title": "Dune", "author": "Frank Herbert"}]
    with patch("mcp_servers.books.server.get_hardcover_client", return_value=mock_client):
        from mcp_servers.books.server import handle_search_books
        result = await handle_search_books({"query": "Dune"})
    assert isinstance(result, list)
    assert result[0]["title"] == "Dune"

@pytest.mark.asyncio
async def test_handle_search_books_propagates_error():
    mock_client = AsyncMock()
    mock_client.search_books.return_value = {
        "error": True, "errorCategory": "transient", "isRetryable": True, "message": "timeout"
    }
    from importlib import reload
    import mcp_servers.books.server as m
    reload(m)
    with patch("mcp_servers.books.server.get_hardcover_client", return_value=mock_client):
        result = await m.handle_search_books({"query": "Dune"})
    assert result["error"] is True
    assert result["isRetryable"] is True

@pytest.mark.asyncio
async def test_handle_get_book_reviews_returns_reviews():
    mock_client = AsyncMock()
    mock_client.get_book_reviews.return_value = [
        {"rating": 5, "review": "Amazing book!", "user": {"username": "reader1"}}
    ]
    from importlib import reload
    import mcp_servers.books.server as m
    reload(m)
    with patch("mcp_servers.books.server.get_hardcover_client", return_value=mock_client):
        result = await m.handle_get_book_reviews({"book_id": "123", "limit": 10})
    assert isinstance(result, list)
    assert result[0]["rating"] == 5

@pytest.mark.asyncio
async def test_handle_search_reviews_filters_by_keyword():
    mock_client = AsyncMock()
    mock_client.search_books.return_value = [{"id": "1", "title": "Dune"}]
    mock_client.get_book_reviews.return_value = [
        {"review": "great worldbuilding in this book", "rating": 5},
        {"review": "boring story", "rating": 2},
    ]
    from importlib import reload
    import mcp_servers.books.server as m
    reload(m)
    with patch("mcp_servers.books.server.get_hardcover_client", return_value=mock_client):
        result = await m.handle_search_reviews({"query": "worldbuilding"})
    assert isinstance(result, list)
    assert len(result) == 1
    assert "worldbuilding" in result[0]["review"]
