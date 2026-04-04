import sys
from unittest.mock import MagicMock

_databricks_mock = MagicMock()
_databricks_sql_mock = MagicMock()
_databricks_mock.sql = _databricks_sql_mock
sys.modules['databricks'] = _databricks_mock
sys.modules['databricks.sql'] = _databricks_sql_mock

import pytest
from unittest.mock import patch

def test_create_schema_executes_all_three_schemas():
    mock_cursor = MagicMock()
    with patch("workflows.setup_schema.get_connection", return_value=MagicMock(cursor=lambda: mock_cursor)):
        from workflows.setup_schema import create_schema
        create_schema(mock_cursor)
    calls = [str(c) for c in mock_cursor.execute.call_args_list]
    assert any("CREATE SCHEMA IF NOT EXISTS abip.books" in c for c in calls)
    assert any("CREATE SCHEMA IF NOT EXISTS abip.reading" in c for c in calls)
    assert any("CREATE SCHEMA IF NOT EXISTS abip.intelligence" in c for c in calls)

def test_create_schema_creates_all_required_tables():
    mock_cursor = MagicMock()
    with patch("workflows.setup_schema.get_connection", return_value=MagicMock(cursor=lambda: mock_cursor)):
        from workflows.setup_schema import create_schema
        create_schema(mock_cursor)
    calls = [str(c) for c in mock_cursor.execute.call_args_list]
    required_tables = [
        "abip.books.books",
        "abip.books.authors",
        "abip.books.reviews",
        "abip.books.enrichment_queue",
        "abip.reading.reading_log",
        "abip.reading.reading_sessions",
        "abip.intelligence.reading_briefs",
        "abip.intelligence.audit_log",
    ]
    for table in required_tables:
        assert any(table in c for c in calls), f"Missing DDL for {table}"

def test_create_schema_uses_delta_format():
    mock_cursor = MagicMock()
    with patch("workflows.setup_schema.get_connection", return_value=MagicMock(cursor=lambda: mock_cursor)):
        from workflows.setup_schema import create_schema
        create_schema(mock_cursor)
    calls = [str(c) for c in mock_cursor.execute.call_args_list]
    table_creates = [c for c in calls if "CREATE TABLE" in c]
    assert len(table_creates) >= 8, "Expected at least 8 CREATE TABLE statements"
    assert all("USING DELTA" in c for c in table_creates), "All tables must use USING DELTA"

def test_get_connection_strips_https_prefix():
    with patch.dict("os.environ", {
        "DATABRICKS_HOST": "https://my-workspace.azuredatabricks.net",
        "DATABRICKS_HTTP_PATH": "/sql/1.0/warehouses/abc123",
        "DATABRICKS_TOKEN": "dapi_test_token",
    }):
        with patch("databricks.sql.connect") as mock_connect:
            mock_connect.return_value = MagicMock()
            from importlib import reload
            import workflows.setup_schema as m
            reload(m)
            m.get_connection()
        call_kwargs = mock_connect.call_args[1]
        assert not call_kwargs["server_hostname"].startswith("https://")
        assert call_kwargs["server_hostname"] == "my-workspace.azuredatabricks.net"
