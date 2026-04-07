import asyncio
import concurrent.futures
from typing import Any
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Tool schemas (Anthropic format) ──────────────────────────────────────────

TOOL_SCHEMAS = [
    # Books
    {"name": "search_books", "description": "Search for books by title, author, ISBN, or genre.", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "get_book_details", "description": "Get full metadata for a specific book by its Hardcover book_id.", "input_schema": {"type": "object", "properties": {"book_id": {"type": "string"}}, "required": ["book_id"]}},
    {"name": "get_book_reviews", "description": "Fetch reviews for a book by its Hardcover book_id.", "input_schema": {"type": "object", "properties": {"book_id": {"type": "string"}, "limit": {"type": "integer", "default": 20}}, "required": ["book_id"]}},
    {"name": "search_reviews", "description": "Search reviews by keyword across books matching a query.", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "get_recommendations", "description": "Find books similar to a given title.", "input_schema": {"type": "object", "properties": {"title": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["title"]}},
    {"name": "get_author_details", "description": "Get author biography and bibliography by name.", "input_schema": {"type": "object", "properties": {"author_name": {"type": "string"}}, "required": ["author_name"]}},
    {"name": "get_book_editions", "description": "Get edition info for a book by Hardcover book_id.", "input_schema": {"type": "object", "properties": {"book_id": {"type": "string"}}, "required": ["book_id"]}},
    {"name": "get_trending_books", "description": "Search for popular books, optionally filtered by genre.", "input_schema": {"type": "object", "properties": {"genre": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": []}},
    # Databricks
    {"name": "query_reading_log", "description": "Query your personal reading history. Filter by status (read, reading, want_to_read).", "input_schema": {"type": "object", "properties": {"status": {"type": "string", "enum": ["read", "reading", "want_to_read"]}, "limit": {"type": "integer", "default": 50}}, "required": []}},
    {"name": "get_reading_stats", "description": "Get aggregated reading stats: total books by status.", "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "add_book_to_library", "description": "Add a book to your personal reading library.", "input_schema": {"type": "object", "properties": {"book_id": {"type": "string"}, "title": {"type": "string"}, "status": {"type": "string", "enum": ["read", "reading", "want_to_read"]}}, "required": ["book_id", "title", "status"]}},
    {"name": "update_reading_status", "description": "Update reading status and optionally rating for a book.", "input_schema": {"type": "object", "properties": {"book_id": {"type": "string"}, "status": {"type": "string", "enum": ["read", "reading", "want_to_read"]}, "rating": {"type": "integer", "minimum": 1, "maximum": 5}}, "required": ["book_id", "status"]}},
    {"name": "search_my_library", "description": "Semantic search across your personal library.", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]}},
    {"name": "trigger_enrichment_job", "description": "Trigger AI enrichment for a book.", "input_schema": {"type": "object", "properties": {"book_id": {"type": "string"}}, "required": ["book_id"]}},
    {"name": "get_job_status", "description": "Check status of a Databricks job run.", "input_schema": {"type": "object", "properties": {"run_id": {"type": "string"}}, "required": ["run_id"]}},
    # Annotations
    {"name": "add_annotation", "description": "Save a highlight, note, or quote from a book.", "input_schema": {"type": "object", "properties": {"book_id": {"type": "string"}, "book_title": {"type": "string"}, "annotation_type": {"type": "string", "enum": ["highlight", "note", "quote"]}, "content": {"type": "string"}, "page_number": {"type": "integer"}}, "required": ["book_id", "book_title", "annotation_type", "content"]}},
    {"name": "get_annotations", "description": "Retrieve saved annotations for a book or all books.", "input_schema": {"type": "object", "properties": {"book_id": {"type": "string"}}, "required": []}},
    {"name": "search_annotations", "description": "Search annotations by keyword.", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "add_journal_entry", "description": "Log a reading session with thoughts and mood.", "input_schema": {"type": "object", "properties": {"book_id": {"type": "string"}, "book_title": {"type": "string"}, "session_date": {"type": "string"}, "content": {"type": "string"}, "mood": {"type": "string"}, "pages_read": {"type": "integer"}}, "required": ["book_id", "book_title", "content"]}},
    {"name": "get_journal_entries", "description": "Retrieve reading journal entries.", "input_schema": {"type": "object", "properties": {"book_id": {"type": "string"}}, "required": []}},
]

# ── Tool executor ─────────────────────────────────────────────────────────────

async def execute_tool(name: str, args: dict) -> Any:
    """Route a tool call to the appropriate Python function."""
    from mcp_servers.books.server import TOOL_HANDLERS as BOOKS
    from mcp_servers.annotations.server import TOOL_HANDLERS as ANNOTATIONS
    from mcp_servers.databricks.server import TOOL_HANDLERS as DATABRICKS

    all_handlers = {**BOOKS, **ANNOTATIONS, **DATABRICKS}
    handler = all_handlers.get(name)
    if handler is None:
        return {"error": True, "errorCategory": "validation", "isRetryable": False, "message": f"Unknown tool: {name}"}

    # Books and annotations handlers are async; databricks handlers are sync
    import inspect
    if inspect.iscoroutinefunction(handler):
        return await handler(args)
    else:
        return await asyncio.to_thread(handler, args)


# ── Agent integration ─────────────────────────────────────────────────────────

def get_agent_response(user_message: str) -> str:
    """Call the coordinator agent and return response."""
    from agents.coordinator import route_request

    async def _run():
        return await route_request(
            user_message,
            mcp_tools=TOOL_SCHEMAS,
            tool_executor=execute_tool,
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, _run())
        return future.result()


def init_chat_history() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []


def add_message(role: str, content: str) -> None:
    st.session_state.messages.append({"role": role, "content": content})
