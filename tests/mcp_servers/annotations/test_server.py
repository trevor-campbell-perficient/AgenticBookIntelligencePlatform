import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Mock mcp if not installed
for mod in ['mcp', 'mcp.server', 'mcp.server.stdio', 'mcp.types']:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

@pytest.fixture
def db(tmp_path):
    os.environ["ANNOTATIONS_DB_PATH"] = str(tmp_path / "test.db")
    from mcp_servers.annotations.db import AnnotationsDB
    database = AnnotationsDB(str(tmp_path / "test.db"))
    database.init_schema()
    return database

def test_get_db_creates_directory_and_schema(tmp_path):
    db_path = str(tmp_path / "subdir" / "annotations.db")
    os.environ["ANNOTATIONS_DB_PATH"] = db_path
    from importlib import reload
    import mcp_servers.annotations.server as m
    reload(m)
    db = m.get_db()
    assert os.path.exists(db_path)

@pytest.mark.asyncio
async def test_add_annotation_tool_returns_id(db, tmp_path):
    from importlib import reload
    import mcp_servers.annotations.server as m
    reload(m)
    result = await m.TOOL_HANDLERS["add_annotation"]({
        "book_id": "book1", "book_title": "Dune",
        "annotation_type": "highlight", "content": "I must not fear."
    })
    assert "id" in result
    assert len(result["id"]) > 0

@pytest.mark.asyncio
async def test_get_annotations_tool_returns_list(db, tmp_path):
    # Pre-populate
    db.add_annotation(book_id="b1", book_title="Dune", annotation_type="note", content="Test note")
    from importlib import reload
    import mcp_servers.annotations.server as m
    reload(m)
    result = await m.TOOL_HANDLERS["get_annotations"]({"book_id": "b1"})
    assert isinstance(result, list)
    assert len(result) == 1

@pytest.mark.asyncio
async def test_search_annotations_tool_finds_keyword(db, tmp_path):
    db.add_annotation(book_id="b1", book_title="Dune", annotation_type="note", content="spice melange")
    from importlib import reload
    import mcp_servers.annotations.server as m
    reload(m)
    result = await m.TOOL_HANDLERS["search_annotations"]({"query": "spice"})
    assert isinstance(result, list)
    assert len(result) == 1

@pytest.mark.asyncio
async def test_unknown_tool_returns_validation_error(tmp_path):
    os.environ["ANNOTATIONS_DB_PATH"] = str(tmp_path / "test.db")
    from importlib import reload
    import mcp_servers.annotations.server as m
    reload(m)
    result = await m.call_tool("nonexistent_tool", {})
    assert len(result) == 1
    import json
    data = json.loads(result[0].text)
    assert data["error"] is True
    assert data["errorCategory"] == "validation"
    assert data["isRetryable"] is False


@pytest.mark.asyncio
async def test_add_journal_entry_tool_returns_id(db, tmp_path):
    from importlib import reload
    import mcp_servers.annotations.server as m
    reload(m)
    result = await m.call_tool("add_journal_entry", {
        "book_id": "book1", "book_title": "Dune",
        "session_date": "2026-04-04", "content": "Great reading session."
    })
    assert len(result) == 1
    import json
    data = json.loads(result[0].text)
    assert "id" in data
    assert len(data["id"]) > 0


@pytest.mark.asyncio
async def test_get_journal_entries_tool_returns_list(db, tmp_path):
    db.add_journal_entry(book_id="b1", book_title="Dune", session_date="2026-04-04", content="Reflections")
    from importlib import reload
    import mcp_servers.annotations.server as m
    reload(m)
    result = await m.call_tool("get_journal_entries", {"book_id": "b1"})
    assert len(result) == 1
    import json
    data = json.loads(result[0].text)
    assert isinstance(data, list)
    assert len(data) == 1
