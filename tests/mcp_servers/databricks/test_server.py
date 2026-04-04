import pytest
import sys
import json
from unittest.mock import MagicMock, patch, AsyncMock

# Mock mcp and databricks if not installed
for mod in ['mcp', 'mcp.server', 'mcp.server.stdio', 'mcp.types']:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

@pytest.mark.asyncio
async def test_query_reading_log_tool_returns_list():
    mock_books = [{"entry_id": "1", "title": "Dune", "status": "read"}]
    with patch("mcp_servers.databricks.db_client.query_reading_log", return_value=mock_books):
        from importlib import reload
        import mcp_servers.databricks.server as m
        reload(m)
        result = m.TOOL_HANDLERS["query_reading_log"]({"status": "read"})
    assert isinstance(result, list)
    assert result[0]["title"] == "Dune"

@pytest.mark.asyncio
async def test_get_reading_stats_tool_returns_dict():
    mock_stats = {"read": 42, "reading": 3, "want_to_read": 15}
    with patch("mcp_servers.databricks.db_client.get_reading_stats", return_value=mock_stats):
        from importlib import reload
        import mcp_servers.databricks.server as m
        reload(m)
        result = m.TOOL_HANDLERS["get_reading_stats"]({})
    assert result["read"] == 42

@pytest.mark.asyncio
async def test_add_book_to_library_tool_returns_entry():
    mock_entry = {"entry_id": "abc-123", "book_id": "1", "title": "Dune", "status": "want_to_read"}
    with patch("mcp_servers.databricks.db_client.add_book_to_library", return_value=mock_entry):
        from importlib import reload
        import mcp_servers.databricks.server as m
        reload(m)
        result = m.TOOL_HANDLERS["add_book_to_library"]({"book_id": "1", "title": "Dune", "status": "want_to_read"})
    assert result["entry_id"] == "abc-123"

@pytest.mark.asyncio
async def test_search_my_library_returns_not_implemented_error():
    from importlib import reload
    import mcp_servers.databricks.server as m
    reload(m)
    result = m.TOOL_HANDLERS["search_my_library"]({"query": "sci-fi survival"})
    assert result.get("error") is True
    assert "Vector search" in result["message"]

@pytest.mark.asyncio
async def test_unknown_tool_returns_validation_error():
    from importlib import reload
    import mcp_servers.databricks.server as m
    reload(m)
    result = m.TOOL_HANDLERS.get("nonexistent_tool")
    assert result is None  # Not in handlers dict
