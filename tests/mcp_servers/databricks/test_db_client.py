import pytest
import sys
from unittest.mock import MagicMock, patch
from contextlib import contextmanager as cm

# Mock databricks if not installed
if 'databricks' not in sys.modules:
    db_mock = MagicMock()
    sys.modules['databricks'] = db_mock
    sys.modules['databricks.sql'] = db_mock.sql
    sys.modules['databricks.sdk'] = db_mock.sdk

def test_get_reading_stats_returns_dict_keyed_by_status():
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [("read", 12), ("reading", 2), ("want_to_read", 45)]
    mock_cursor.description = [("status",), ("count",)]
    with patch("mcp_servers.databricks.db_client.get_cursor") as mock_get_cursor:
        mock_get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
        from mcp_servers.databricks.db_client import get_reading_stats
        result = get_reading_stats()
    assert result["read"] == 12
    assert result["reading"] == 2
    assert result["want_to_read"] == 45

def test_query_reading_log_uses_parameterized_sql_for_status():
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_cursor.description = [("entry_id",), ("title",), ("status",)]
    with patch("mcp_servers.databricks.db_client.get_cursor") as mock_get_cursor:
        mock_get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
        from mcp_servers.databricks.db_client import query_reading_log
        query_reading_log(status="read")
    call_args = mock_cursor.execute.call_args
    sql_str = call_args[0][0]
    params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get('parameters', ())
    # Status value must be in params, not embedded as a literal in the SQL string
    assert "%s" in sql_str or "?" in sql_str
    # The status value "read" must not appear as a quoted literal in the SQL
    assert "'read'" not in sql_str and '"read"' not in sql_str

def test_add_book_to_library_returns_entry_with_id():
    mock_cursor = MagicMock()
    with patch("mcp_servers.databricks.db_client.get_cursor") as mock_get_cursor:
        mock_get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
        from mcp_servers.databricks.db_client import add_book_to_library
        result = add_book_to_library(book_id="book123", title="Dune", status="read")
    assert result["book_id"] == "book123"
    assert result["title"] == "Dune"
    assert result["status"] == "read"
    assert "entry_id" in result
    assert len(result["entry_id"]) > 0

def test_update_reading_status_with_rating_uses_parameterized_sql():
    mock_cursor = MagicMock()
    with patch("mcp_servers.databricks.db_client.get_cursor") as mock_get_cursor:
        mock_get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_get_cursor.return_value.__exit__ = MagicMock(return_value=False)
        from mcp_servers.databricks.db_client import update_reading_status
        result = update_reading_status(book_id="book123", status="read", rating=5)
    call_args = mock_cursor.execute.call_args
    sql_str = call_args[0][0]
    assert "%s" in sql_str or "?" in sql_str
    assert "book123" not in sql_str
    assert result["status"] == "read"
    assert result["rating"] == 5

def test_get_connection_validates_env_vars():
    with patch.dict("os.environ", {}, clear=True):
        from importlib import reload
        import mcp_servers.databricks.db_client as m
        reload(m)
        with pytest.raises(EnvironmentError, match="Missing required environment variables"):
            m.get_connection()
