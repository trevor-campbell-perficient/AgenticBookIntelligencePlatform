import os
import asyncio
import json
from typing import Any
from dotenv import load_dotenv

load_dotenv()

# Lazy MCP imports to allow testing without mcp installed
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    Server = object
    types = None

from mcp_servers.books.hardcover_client import HardcoverClient

if _MCP_AVAILABLE:
    app = Server("books-api")
else:
    app = object()

_hardcover_client: HardcoverClient | None = None


def get_hardcover_client() -> HardcoverClient:
    global _hardcover_client
    if _hardcover_client is None:
        api_key = os.environ.get("HARDCOVER_API_KEY", "")
        if not api_key:
            raise EnvironmentError("HARDCOVER_API_KEY not set. See .env.example.")
        _hardcover_client = HardcoverClient(api_key=api_key)
    return _hardcover_client


async def handle_search_books(args: dict[str, Any]) -> list[dict] | dict:
    client = get_hardcover_client()
    return await client.search_books(args["query"])


async def handle_get_book_details(args: dict[str, Any]) -> dict:
    client = get_hardcover_client()
    return await client.get_book_details(int(args["book_id"]))


async def handle_get_book_reviews(args: dict[str, Any]) -> list[dict] | dict:
    client = get_hardcover_client()
    return await client.get_book_reviews(int(args["book_id"]), int(args.get("limit", 20)))


async def handle_search_reviews(args: dict[str, Any]) -> list[dict] | dict:
    """Search reviews by keyword across multiple books."""
    query = args["query"]
    client = get_hardcover_client()
    books = await client.search_books(query)
    if isinstance(books, dict) and books.get("error"):
        return books
    results = []
    for book in books[:3]:
        reviews = await client.get_book_reviews(int(book["id"]), limit=10)
        if isinstance(reviews, list):
            for r in reviews:
                if query.lower() in str(r.get("review", "")).lower():
                    results.append({"book_title": book["title"], **r})
    return results


async def handle_get_author_details(args: dict[str, Any]) -> dict:
    client = get_hardcover_client()
    return await client.get_author_details(args["author_name"])


async def handle_get_book_editions(args: dict[str, Any]) -> list[dict] | dict:
    # Editions via Hardcover book details — extract edition info
    client = get_hardcover_client()
    details = await client.get_book_details(int(args["book_id"]))
    if isinstance(details, dict) and details.get("error"):
        return details
    return [details]  # Single edition from Hardcover; Open Library integration in Phase 2


async def handle_get_recommendations(args: dict[str, Any]) -> list[dict] | dict:
    client = get_hardcover_client()
    results = await client.search_books(args["title"])
    if isinstance(results, dict) and results.get("error"):
        return results
    limit = int(args.get("limit", 10))
    return results[:limit]


async def handle_get_trending_books(args: dict[str, Any]) -> list[dict] | dict:
    client = get_hardcover_client()
    genre = args.get("genre", "")
    query = f"trending {genre}".strip()
    results = await client.search_books(query)
    if isinstance(results, dict) and results.get("error"):
        return results
    limit = int(args.get("limit", 10))
    return results[:limit]


TOOL_HANDLERS = {
    "search_books": handle_search_books,
    "get_book_details": handle_get_book_details,
    "get_book_reviews": handle_get_book_reviews,
    "search_reviews": handle_search_reviews,
    "get_author_details": handle_get_author_details,
    "get_book_editions": handle_get_book_editions,
    "get_recommendations": handle_get_recommendations,
    "get_trending_books": handle_get_trending_books,
}


if _MCP_AVAILABLE:
    @app.list_tools()
    async def list_tools() -> list:  # list[types.Tool] when MCP available
        return [
            types.Tool(
                name="search_books",
                description="Search for books by title, author, ISBN, or genre. Returns list of matching books with id, title, author. Use when finding books matching a query. Different from get_book_details which fetches full info for a known book id.",
                inputSchema={"type": "object", "properties": {"query": {"type": "string", "description": "Search query — title, author name, ISBN, or genre"}}, "required": ["query"]},
            ),
            types.Tool(
                name="get_book_details",
                description="Get full metadata for a specific book by its Hardcover book_id. Returns description, ratings, page count, cover URL, release date. Use after search_books when you have a known book id.",
                inputSchema={"type": "object", "properties": {"book_id": {"type": "string", "description": "Hardcover integer book ID, obtained from search_books results"}}, "required": ["book_id"]},
            ),
            types.Tool(
                name="get_book_reviews",
                description="Fetch all reviews for one specific book by its Hardcover book_id. Returns reviewer, rating, review text. Use when you want all reviews for a single known book. Different from search_reviews which searches review text by keyword across multiple books.",
                inputSchema={"type": "object", "properties": {"book_id": {"type": "string"}, "limit": {"type": "integer", "default": 20}}, "required": ["book_id"]},
            ),
            types.Tool(
                name="search_reviews",
                description="Search reviews of books matching a title/topic query. Finds books matching the query, then filters their reviews for the given keyword. Use for 'find reviews mentioning X in books about Y'. Different from get_book_reviews which fetches all reviews for one specific known book_id.",
                inputSchema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            ),
            types.Tool(
                name="get_recommendations",
                description="Find books similar to or related to a given title by searching the catalog. Returns books with similar titles or by the same author. Note: results are search-based, not algorithmically recommended.",
                inputSchema={"type": "object", "properties": {"title": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["title"]},
            ),
            types.Tool(
                name="get_author_details",
                description="Get author biography, bibliography, and similar authors by author name.",
                inputSchema={"type": "object", "properties": {"author_name": {"type": "string"}}, "required": ["author_name"]},
            ),
            types.Tool(
                name="get_book_editions",
                description="Get edition information for a book by its Hardcover book_id. Currently returns primary edition details. Full multi-edition support (formats, languages, publishers) planned for Phase 2 with Open Library integration.",
                inputSchema={"type": "object", "properties": {"book_id": {"type": "string"}}, "required": ["book_id"]},
            ),
            types.Tool(
                name="get_trending_books",
                description="Search for popular or trending books, optionally filtered by genre keyword. Results are based on catalog search — use for discovering books in a genre rather than real-time trending data.",
                inputSchema={"type": "object", "properties": {"genre": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": []},
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list:  # list[types.TextContent] when MCP available
        handler = TOOL_HANDLERS.get(name)
        if not handler:
            result = {"error": True, "errorCategory": "validation", "isRetryable": False, "message": f"Unknown tool: {name}"}
        else:
            try:
                result = await handler(arguments)
            except Exception as e:
                result = {"error": True, "errorCategory": "transient", "isRetryable": True, "message": str(e)}
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def main() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    if __name__ == "__main__":
        asyncio.run(main())
