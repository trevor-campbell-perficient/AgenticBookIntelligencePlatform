import os
import asyncio
import json
from typing import Any
from dotenv import load_dotenv

load_dotenv()

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    Server = object
    types = None


class _TextContent:
    """Fallback TextContent used when mcp is not installed (e.g. during tests)."""
    def __init__(self, *, type: str, text: str) -> None:
        self.type = type
        self.text = text

from mcp_servers.annotations.db import AnnotationsDB

if _MCP_AVAILABLE:
    app = Server("annotations")
else:
    app = object()


def get_db() -> AnnotationsDB:
    db_path = os.environ.get("ANNOTATIONS_DB_PATH", "data/annotations.db")
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    db = AnnotationsDB(db_path)
    db.init_schema()
    return db


async def _handle_add_annotation(args: dict[str, Any]) -> dict[str, Any]:
    db = get_db()
    annotation_id = db.add_annotation(**args)
    return {"id": annotation_id}


async def _handle_get_annotations(args: dict[str, Any]) -> list[dict[str, Any]]:
    db = get_db()
    return db.get_annotations(book_id=args.get("book_id"))


async def _handle_search_annotations(args: dict[str, Any]) -> list[dict[str, Any]]:
    db = get_db()
    return db.search_annotations(args["query"])


async def _handle_add_journal_entry(args: dict[str, Any]) -> dict[str, Any]:
    db = get_db()
    entry_id = db.add_journal_entry(**args)
    return {"id": entry_id}


async def _handle_get_journal_entries(args: dict[str, Any]) -> list[dict[str, Any]]:
    db = get_db()
    return db.get_journal_entries(book_id=args.get("book_id"))


TOOL_HANDLERS = {
    "add_annotation": _handle_add_annotation,
    "get_annotations": _handle_get_annotations,
    "search_annotations": _handle_search_annotations,
    "add_journal_entry": _handle_add_journal_entry,
    "get_journal_entries": _handle_get_journal_entries,
}


async def call_tool(name: str, arguments: dict) -> list:
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        result: Any = {"error": True, "errorCategory": "validation", "isRetryable": False, "message": f"Unknown tool: {name}"}
    else:
        try:
            result = await handler(arguments)
        except Exception as e:
            result = {"error": True, "errorCategory": "transient", "isRetryable": True, "message": str(e)}
    return [_TextContent(type="text", text=json.dumps(result, default=str, indent=2))]


if _MCP_AVAILABLE:
    @app.list_tools()
    async def list_tools() -> list:
        return [
            types.Tool(
                name="add_annotation",
                description="Save a highlight, note, or quote from a book with optional page number. Use to capture important passages or thoughts while reading.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "book_id": {"type": "string", "description": "Hardcover book ID"},
                        "book_title": {"type": "string"},
                        "annotation_type": {"type": "string", "enum": ["highlight", "note", "quote"]},
                        "content": {"type": "string", "description": "The text to save"},
                        "page_number": {"type": "integer", "description": "Optional page number"},
                    },
                    "required": ["book_id", "book_title", "annotation_type", "content"],
                },
            ),
            types.Tool(
                name="get_annotations",
                description="Retrieve saved annotations (highlights, notes, quotes) for a specific book or all books. Different from search_annotations which does keyword search.",
                inputSchema={
                    "type": "object",
                    "properties": {"book_id": {"type": "string", "description": "Hardcover book ID. Omit to retrieve all annotations."}},
                    "required": [],
                },
            ),
            types.Tool(
                name="search_annotations",
                description="Search annotations by keyword using pattern matching against content and book title. Case-insensitive for ASCII characters. Use to find annotations mentioning a specific concept or phrase. Different from get_annotations which retrieves all annotations for a book.",
                inputSchema={
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "Keyword or phrase to search for"}},
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="add_journal_entry",
                description="Log a reading session with date, thoughts, mood, and pages read. Use to record reflections after a reading session.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "book_id": {"type": "string"},
                        "book_title": {"type": "string"},
                        "session_date": {"type": "string", "description": "ISO date YYYY-MM-DD"},
                        "content": {"type": "string", "description": "Session thoughts and reflections"},
                        "mood": {"type": "string", "description": "Reading mood (e.g. focused, tired, engaged)"},
                        "pages_read": {"type": "integer"},
                    },
                    "required": ["book_id", "book_title", "session_date", "content"],
                },
            ),
            types.Tool(
                name="get_journal_entries",
                description="Retrieve reading journal entries for a specific book or all journal entries. Returns session dates, mood, pages read, and reflections.",
                inputSchema={
                    "type": "object",
                    "properties": {"book_id": {"type": "string", "description": "Omit to retrieve all journal entries"}},
                    "required": [],
                },
            ),
        ]

    app.call_tool()(call_tool)

    async def main() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    if __name__ == "__main__":
        asyncio.run(main())
