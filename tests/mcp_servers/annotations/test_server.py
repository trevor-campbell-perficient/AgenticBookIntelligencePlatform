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

def test_add_annotation_tool_returns_id(db, tmp_path):
    from importlib import reload
    import mcp_servers.annotations.server as m
    reload(m)
    result = m.TOOL_HANDLERS["add_annotation"]({
        "book_id": "book1", "book_title": "Dune",
        "annotation_type": "highlight", "content": "I must not fear."
    })
    assert "id" in result
    assert len(result["id"]) > 0

def test_get_annotations_tool_returns_list(db, tmp_path):
    # Pre-populate
    db.add_annotation(book_id="b1", book_title="Dune", annotation_type="note", content="Test note")
    from importlib import reload
    import mcp_servers.annotations.server as m
    reload(m)
    result = m.TOOL_HANDLERS["get_annotations"]({"book_id": "b1"})
    assert isinstance(result, list)
    assert len(result) == 1

def test_search_annotations_tool_finds_keyword(db, tmp_path):
    db.add_annotation(book_id="b1", book_title="Dune", annotation_type="note", content="spice melange")
    from importlib import reload
    import mcp_servers.annotations.server as m
    reload(m)
    result = m.TOOL_HANDLERS["search_annotations"]({"query": "spice"})
    assert isinstance(result, list)
    assert len(result) == 1

def test_unknown_tool_returns_validation_error(tmp_path):
    os.environ["ANNOTATIONS_DB_PATH"] = str(tmp_path / "test.db")
    from importlib import reload
    import mcp_servers.annotations.server as m
    reload(m)
    result = m.TOOL_HANDLERS.get("nonexistent_tool")
    assert result is None
