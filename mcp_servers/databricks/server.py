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

from mcp_servers.databricks import db_client
from mcp_servers.databricks.job_client import trigger_enrichment, get_job_status

if _MCP_AVAILABLE:
    app = Server("databricks")
else:
    app = object()


def _handle_query_reading_log(args: dict[str, Any]) -> list | dict:
    return db_client.query_reading_log(**args)


def _handle_get_reading_stats(args: dict[str, Any]) -> dict:
    return db_client.get_reading_stats()


def _handle_add_book_to_library(args: dict[str, Any]) -> dict:
    return db_client.add_book_to_library(**args)


def _handle_update_reading_status(args: dict[str, Any]) -> dict:
    return db_client.update_reading_status(**args)


def _handle_search_my_library(args: dict[str, Any]) -> dict:
    return {
        "error": True,
        "errorCategory": "transient",
        "isRetryable": False,
        "message": (
            "Vector search not yet implemented — requires FM index setup in Databricks workspace."
        ),
    }


def _handle_trigger_enrichment_job(args: dict[str, Any]) -> dict:
    return trigger_enrichment(args["book_id"])


def _handle_get_job_status(args: dict[str, Any]) -> dict:
    return get_job_status(args["run_id"])


TOOL_HANDLERS = {
    "query_reading_log": _handle_query_reading_log,
    "get_reading_stats": _handle_get_reading_stats,
    "add_book_to_library": _handle_add_book_to_library,
    "update_reading_status": _handle_update_reading_status,
    "search_my_library": _handle_search_my_library,
    "trigger_enrichment_job": _handle_trigger_enrichment_job,
    "get_job_status": _handle_get_job_status,
}


if _MCP_AVAILABLE:
    @app.list_tools()
    async def list_tools() -> list:
        return [
            types.Tool(
                name="query_reading_log",
                description=(
                    "Query your personal reading history from Delta Lake. Filter by status "
                    "(read, reading, want_to_read). Returns books with title, status, rating, "
                    "and dates. Use for 'what have I read?' questions. Different from "
                    "search_my_library which does semantic search by topic."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["read", "reading", "want_to_read"],
                            "description": "Filter by reading status. Omit to return all.",
                        },
                        "limit": {
                            "type": "integer",
                            "default": 50,
                            "description": "Max rows to return",
                        },
                    },
                    "required": [],
                },
            ),
            types.Tool(
                name="get_reading_stats",
                description=(
                    "Get aggregated reading statistics: total books by status, count by genre, "
                    "average rating. Use for 'how many books did I read?' or to populate "
                    "dashboard data. Returns a summary dict, not individual book records."
                ),
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            types.Tool(
                name="add_book_to_library",
                description=(
                    "Add a new book to your personal reading library with a status. Use after "
                    "confirming book details with search_books from the books server. Requires "
                    "book_id (from Hardcover), title, and status."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "book_id": {
                            "type": "string",
                            "description": "Hardcover book ID from search_books",
                        },
                        "title": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["read", "reading", "want_to_read"],
                        },
                    },
                    "required": ["book_id", "title", "status"],
                },
            ),
            types.Tool(
                name="update_reading_status",
                description=(
                    "Update the reading status and optionally a 1-5 rating for a book already "
                    "in your library. Use when finishing a book (set status=read, add rating) "
                    "or starting one (set status=reading)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "book_id": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["read", "reading", "want_to_read"],
                        },
                        "rating": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 5,
                            "description": "Optional 1-5 rating",
                        },
                    },
                    "required": ["book_id", "status"],
                },
            ),
            types.Tool(
                name="search_my_library",
                description=(
                    "Semantic vector search across your personal library using natural language "
                    "(e.g. 'books about survival in space', 'epic fantasy with magic systems'). "
                    "Uses FM embeddings. Different from query_reading_log which filters by exact "
                    "status value. Note: requires FM index setup — returns error if not yet "
                    "configured."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language description of books to find",
                        },
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="trigger_enrichment_job",
                description=(
                    "Trigger the Databricks enrichment workflow to generate an AI reading brief "
                    "and vector embeddings for a specific book. Returns a run_id to track "
                    "progress with get_job_status."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "book_id": {
                            "type": "string",
                            "description": "Hardcover book ID to enrich",
                        }
                    },
                    "required": ["book_id"],
                },
            ),
            types.Tool(
                name="get_job_status",
                description=(
                    "Check the current status of a Databricks workflow job run using the run_id "
                    "returned by trigger_enrichment_job. Returns life_cycle_state "
                    "(RUNNING, TERMINATED, etc.) and result_state (SUCCESS, FAILED)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "run_id": {
                            "type": "string",
                            "description": "Run ID returned by trigger_enrichment_job",
                        }
                    },
                    "required": ["run_id"],
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list:
        handler = TOOL_HANDLERS.get(name)
        if not handler:
            result = {
                "error": True,
                "errorCategory": "validation",
                "isRetryable": False,
                "message": f"Unknown tool: {name}",
            }
        else:
            try:
                result = handler(arguments)
            except Exception as e:
                result = {
                    "error": True,
                    "errorCategory": "transient",
                    "isRetryable": False,
                    "message": str(e),
                }
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def main() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    if __name__ == "__main__":
        asyncio.run(main())
