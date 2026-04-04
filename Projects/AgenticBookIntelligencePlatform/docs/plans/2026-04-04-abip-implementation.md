# Agentic Book Intelligence Platform — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:executing-plans to implement this plan task-by-task.

**Goal:** Build a multi-agent book intelligence platform on Databricks that demonstrates every domain of the Claude Certified Architect: Foundations certification exam.

**Architecture:** A Claude SDK coordinator agent routes requests to three specialized subagents (Book Discovery, Data Intelligence, Synthesis), each backed by a dedicated MCP server. A Streamlit Databricks App provides the UI, Delta Lake stores all data, and Databricks Workflows handle scheduled jobs.

**Tech Stack:** Python 3.11+, Anthropic SDK (`anthropic`), MCP Python SDK (`mcp`), Databricks SDK (`databricks-sdk`), Databricks SQL Connector (`databricks-sql-connector`), Streamlit, httpx, SQLite3, pytest, GitHub Actions

**Reference:** `docs/plans/2026-04-04-abip-design.md`

---

## Task 1: Project Scaffold

**Files:**
- Create: `CLAUDE.md`
- Create: `.mcp.json`
- Create: `.env.example`
- Create: `requirements.txt`
- Create: `.claude/rules/databricks.md`
- Create: `.claude/rules/mcp-servers.md`
- Create: `.claude/commands/sync-books.md`
- Create: `.claude/commands/run-enrichment.md`
- Create: `.claude/commands/generate-digest.md`
- Create: `mcp_servers/books/__init__.py`
- Create: `mcp_servers/databricks/__init__.py`
- Create: `mcp_servers/annotations/__init__.py`
- Create: `agents/__init__.py`
- Create: `app/__init__.py`
- Create: `workflows/__init__.py`
- Create: `tests/__init__.py`

**Step 1: Create directory structure**

```bash
mkdir -p mcp_servers/books mcp_servers/databricks mcp_servers/annotations
mkdir -p agents app workflows
mkdir -p tests/mcp_servers/books tests/mcp_servers/databricks tests/mcp_servers/annotations
mkdir -p tests/agents
mkdir -p .claude/rules .claude/commands
touch mcp_servers/books/__init__.py mcp_servers/databricks/__init__.py mcp_servers/annotations/__init__.py
touch agents/__init__.py app/__init__.py workflows/__init__.py tests/__init__.py
```

**Step 2: Create `CLAUDE.md`**

```markdown
# Agentic Book Intelligence Platform

## Project Overview
Multi-agent book intelligence system using Claude SDK, 3 MCP servers, Databricks backend, and Streamlit app.
See `docs/plans/2026-04-04-abip-design.md` for full architecture.

## Tech Stack
- Python 3.11+
- Anthropic SDK for Claude claude-sonnet-4-6 coordinator + subagents
- MCP Python SDK for 3 MCP servers
- Databricks SDK + SQL Connector for Delta Lake
- Streamlit deployed on Databricks Apps

## Coding Standards
- All async where possible (httpx, asyncio)
- Type hints on all function signatures
- Structured error responses from all MCP tools: `{"error": true, "errorCategory": "...", "isRetryable": bool, "message": "..."}`
- No secrets in code — use environment variables
- pytest for all tests; run with `pytest tests/ -v`

## MCP Server Pattern
Each MCP server lives in `mcp_servers/<name>/server.py`. Run with:
`python mcp_servers/<name>/server.py`

## Agent Pattern
Coordinator in `agents/coordinator.py`. Subagents in `agents/<name>_agent.py`.
All agents use `anthropic` SDK with `claude-sonnet-4-6`.

## Environment Variables
See `.env.example` for all required vars. Copy to `.env` and fill in values.
```

**Step 3: Create `.mcp.json`**

```json
{
  "mcpServers": {
    "books": {
      "command": "python",
      "args": ["mcp_servers/books/server.py"],
      "env": {
        "HARDCOVER_API_KEY": "${HARDCOVER_API_KEY}",
        "GOOGLE_BOOKS_API_KEY": "${GOOGLE_BOOKS_API_KEY}"
      }
    },
    "databricks": {
      "command": "python",
      "args": ["mcp_servers/databricks/server.py"],
      "env": {
        "DATABRICKS_HOST": "${DATABRICKS_HOST}",
        "DATABRICKS_TOKEN": "${DATABRICKS_TOKEN}",
        "DATABRICKS_HTTP_PATH": "${DATABRICKS_HTTP_PATH}"
      }
    },
    "annotations": {
      "command": "python",
      "args": ["mcp_servers/annotations/server.py"],
      "env": {
        "ANNOTATIONS_DB_PATH": "${ANNOTATIONS_DB_PATH}"
      }
    }
  }
}
```

**Step 4: Create `.env.example`**

```bash
# Claude API
ANTHROPIC_API_KEY=your_anthropic_api_key

# Book APIs
HARDCOVER_API_KEY=your_hardcover_api_key
GOOGLE_BOOKS_API_KEY=your_google_books_api_key

# Databricks
DATABRICKS_HOST=https://your-workspace.azuredatabricks.net
DATABRICKS_TOKEN=your_databricks_pat
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your_warehouse_id
DATABRICKS_CATALOG=abip
DATABRICKS_CLUSTER_ID=your_cluster_id

# Annotations
ANNOTATIONS_DB_PATH=data/annotations.db
```

**Step 5: Create `requirements.txt`**

```
anthropic>=0.40.0
mcp>=1.0.0
databricks-sdk>=0.20.0
databricks-sql-connector>=3.0.0
streamlit>=1.35.0
httpx>=0.27.0
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-mock>=3.12.0
plotly>=5.20.0
pandas>=2.2.0
```

**Step 6: Create `.claude/rules/databricks.md`**

```yaml
---
paths: ["**/*.py", "workflows/**/*"]
---
# Databricks Rules

- Use `databricks-sdk` for job management and cluster operations
- Use `databricks-sql-connector` for SQL queries against Delta tables
- Always use parameterized queries — never f-string SQL
- Catalog: `abip`, schemas: `books`, `reading`, `intelligence`
- Delta table writes: use `MERGE INTO` for upserts, not `INSERT OVERWRITE`
- Test SQL queries against the warehouse before embedding in code
```

**Step 7: Create `.claude/rules/mcp-servers.md`**

```yaml
---
paths: ["mcp_servers/**/*"]
---
# MCP Server Rules

- All tools must return structured errors: `{"error": true, "errorCategory": "transient|validation|permission|business", "isRetryable": bool, "message": "..."}`
- Tool descriptions must clearly differentiate from similar tools — include input format, example, and when-to-use-vs-alternative
- Never raise unhandled exceptions from tool handlers — catch and return structured error
- Each server runs on stdio transport (default MCP)
- Test each tool handler independently before integration testing
```

**Step 8: Create custom slash commands**

`.claude/commands/sync-books.md`:
```markdown
Trigger the Databricks nightly book sync job manually.
Run: check job status at workflows/job_sync.py, then trigger via Databricks SDK.
Report the job run ID and current status.
```

`.claude/commands/run-enrichment.md`:
```markdown
Trigger the book enrichment pipeline for any books in the enrichment queue.
Query `abip.books.enrichment_queue` for pending items, then trigger the enrichment workflow.
```

`.claude/commands/generate-digest.md`:
```markdown
Generate the weekly reading digest now (don't wait for Sunday schedule).
Call the digest workflow directly and display the output.
```

**Step 9: Commit**

```bash
git add .
git commit -m "feat: project scaffold — CLAUDE.md, .mcp.json, directory structure, slash commands"
```

---

## Task 2: Unity Catalog Schema Setup

**Files:**
- Create: `workflows/setup_schema.py`
- Create: `tests/test_setup_schema.py`

**Step 1: Write failing test**

```python
# tests/test_setup_schema.py
import pytest
from unittest.mock import MagicMock, patch

def test_create_catalog_executes_sql():
    mock_cursor = MagicMock()
    with patch("workflows.setup_schema.get_connection", return_value=MagicMock(cursor=lambda: mock_cursor)):
        from workflows.setup_schema import create_schema
        create_schema(mock_cursor)
    calls = [str(c) for c in mock_cursor.execute.call_args_list]
    assert any("CREATE SCHEMA IF NOT EXISTS abip.books" in c for c in calls)
    assert any("CREATE SCHEMA IF NOT EXISTS abip.reading" in c for c in calls)
    assert any("CREATE SCHEMA IF NOT EXISTS abip.intelligence" in c for c in calls)
```

**Step 2: Run to verify it fails**

```bash
pytest tests/test_setup_schema.py -v
```
Expected: `ModuleNotFoundError` or `ImportError`

**Step 3: Implement `workflows/setup_schema.py`**

```python
import os
from databricks import sql
from dotenv import load_dotenv

load_dotenv()

DDL = [
    "CREATE CATALOG IF NOT EXISTS abip",
    "CREATE SCHEMA IF NOT EXISTS abip.books",
    "CREATE SCHEMA IF NOT EXISTS abip.reading",
    "CREATE SCHEMA IF NOT EXISTS abip.intelligence",

    """CREATE TABLE IF NOT EXISTS abip.books.books (
        book_id STRING NOT NULL,
        title STRING,
        authors ARRAY<STRING>,
        isbn STRING,
        isbn13 STRING,
        description STRING,
        genres ARRAY<STRING>,
        page_count INT,
        published_date STRING,
        cover_url STRING,
        average_rating DOUBLE,
        ratings_count INT,
        source STRING,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.books.authors (
        author_id STRING NOT NULL,
        name STRING,
        bio STRING,
        similar_authors ARRAY<STRING>,
        source STRING,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.books.reviews (
        review_id STRING NOT NULL,
        book_id STRING,
        reviewer STRING,
        rating INT,
        review_text STRING,
        review_date STRING,
        source STRING,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.books.enrichment_queue (
        book_id STRING NOT NULL,
        status STRING DEFAULT 'pending',
        queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.reading.reading_log (
        entry_id STRING NOT NULL,
        book_id STRING,
        title STRING,
        status STRING,
        rating INT,
        started_date STRING,
        finished_date STRING,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.reading.reading_sessions (
        session_id STRING NOT NULL,
        book_id STRING,
        session_date STRING,
        pages_read INT,
        notes STRING,
        mood STRING,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.intelligence.reading_briefs (
        book_id STRING NOT NULL,
        brief_text STRING,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.intelligence.audit_log (
        log_id STRING NOT NULL,
        session_id STRING,
        tool_name STRING,
        tool_input STRING,
        tool_result STRING,
        called_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",
]

def get_connection():
    return sql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"].replace("https://", ""),
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        access_token=os.environ["DATABRICKS_TOKEN"],
    )

def create_schema(cursor):
    for stmt in DDL:
        cursor.execute(stmt)

if __name__ == "__main__":
    conn = get_connection()
    with conn.cursor() as cursor:
        create_schema(cursor)
    print("Schema setup complete.")
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_setup_schema.py -v
```
Expected: PASS

**Step 5: Run schema setup against real workspace**

```bash
python workflows/setup_schema.py
```
Expected: "Schema setup complete."

**Step 6: Commit**

```bash
git add workflows/setup_schema.py tests/test_setup_schema.py
git commit -m "feat: Unity Catalog schema setup — books, reading, intelligence schemas + Delta tables"
```

---

## Task 3: MCP Server #1 — Books API

**Files:**
- Create: `mcp_servers/books/server.py`
- Create: `mcp_servers/books/hardcover_client.py`
- Create: `mcp_servers/books/openlibrary_client.py`
- Create: `tests/mcp_servers/books/test_server.py`
- Create: `tests/mcp_servers/books/test_hardcover_client.py`

**Step 1: Write failing tests for Hardcover client**

```python
# tests/mcp_servers/books/test_hardcover_client.py
import pytest
from unittest.mock import AsyncMock, patch
import httpx

@pytest.mark.asyncio
async def test_search_books_returns_results():
    mock_response = {
        "data": {
            "search": {
                "results": [
                    {"book": {"id": "1", "title": "Dune", "contributions": [{"author": {"name": "Frank Herbert"}}]}}
                ]
            }
        }
    }
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(200, json=mock_response)
        from mcp_servers.books.hardcover_client import HardcoverClient
        client = HardcoverClient(api_key="test_key")
        results = await client.search_books("Dune")
    assert len(results) == 1
    assert results[0]["title"] == "Dune"

@pytest.mark.asyncio
async def test_search_books_returns_structured_error_on_failure():
    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("timeout")):
        from mcp_servers.books.hardcover_client import HardcoverClient
        client = HardcoverClient(api_key="test_key")
        result = await client.search_books("Dune")
    assert result["error"] is True
    assert result["errorCategory"] == "transient"
    assert result["isRetryable"] is True
```

**Step 2: Run to verify failure**

```bash
pytest tests/mcp_servers/books/test_hardcover_client.py -v
```
Expected: `ModuleNotFoundError`

**Step 3: Implement `mcp_servers/books/hardcover_client.py`**

```python
import httpx
from typing import Any

HARDCOVER_GRAPHQL_URL = "https://api.hardcover.app/v1/graphql"

SEARCH_QUERY = """
query SearchBooks($query: String!) {
  search(query: $query, query_type: "Book", per_page: 10) {
    results
  }
}
"""

GET_BOOK_QUERY = """
query GetBook($id: Int!) {
  books(where: {id: {_eq: $id}}) {
    id title description pages
    book_series { position series { name } }
    contributions { author { name } }
    ratings_count
    rating
    image { url }
    release_date
  }
}
"""

GET_REVIEWS_QUERY = """
query GetReviews($bookId: Int!, $limit: Int!) {
  user_books(where: {book_id: {_eq: $bookId}, review: {_is_null: false}}, limit: $limit) {
    rating review user { username }
  }
}
"""

class HardcoverClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async def _query(self, query: str, variables: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    HARDCOVER_GRAPHQL_URL,
                    json={"query": query, "variables": variables},
                    headers=self.headers,
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.TimeoutException:
            return {"error": True, "errorCategory": "transient", "isRetryable": True, "message": "Hardcover API timeout"}
        except httpx.HTTPStatusError as e:
            return {"error": True, "errorCategory": "transient", "isRetryable": True, "message": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"error": True, "errorCategory": "transient", "isRetryable": False, "message": str(e)}

    async def search_books(self, query: str) -> list[dict] | dict:
        result = await self._query(SEARCH_QUERY, {"query": query})
        if "error" in result:
            return result
        try:
            results = result["data"]["search"]["results"]
            return [{"id": str(r.get("id", "")), "title": r.get("title", ""), "author": r.get("author_names", [""])[0] if r.get("author_names") else ""} for r in (results if isinstance(results, list) else [])]
        except (KeyError, TypeError):
            return {"error": True, "errorCategory": "transient", "isRetryable": True, "message": "Unexpected response structure"}

    async def get_book_details(self, book_id: int) -> dict:
        result = await self._query(GET_BOOK_QUERY, {"id": book_id})
        if "error" in result:
            return result
        try:
            books = result["data"]["books"]
            if not books:
                return {"error": True, "errorCategory": "validation", "isRetryable": False, "message": f"Book {book_id} not found"}
            return books[0]
        except (KeyError, TypeError) as e:
            return {"error": True, "errorCategory": "transient", "isRetryable": True, "message": str(e)}

    async def get_book_reviews(self, book_id: int, limit: int = 20) -> list[dict] | dict:
        result = await self._query(GET_REVIEWS_QUERY, {"bookId": book_id, "limit": limit})
        if "error" in result:
            return result
        try:
            return result["data"]["user_books"]
        except (KeyError, TypeError) as e:
            return {"error": True, "errorCategory": "transient", "isRetryable": True, "message": str(e)}
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/mcp_servers/books/test_hardcover_client.py -v
```
Expected: PASS

**Step 5: Write failing tests for MCP server tools**

```python
# tests/mcp_servers/books/test_server.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_search_books_tool_returns_list():
    mock_client = AsyncMock()
    mock_client.search_books.return_value = [{"id": "1", "title": "Dune", "author": "Frank Herbert"}]
    with patch("mcp_servers.books.server.get_hardcover_client", return_value=mock_client):
        from mcp_servers.books.server import handle_search_books
        result = await handle_search_books({"query": "Dune"})
    assert isinstance(result, list)
    assert result[0]["title"] == "Dune"

@pytest.mark.asyncio
async def test_search_books_tool_propagates_error():
    mock_client = AsyncMock()
    mock_client.search_books.return_value = {"error": True, "errorCategory": "transient", "isRetryable": True, "message": "timeout"}
    with patch("mcp_servers.books.server.get_hardcover_client", return_value=mock_client):
        from mcp_servers.books.server import handle_search_books
        result = await handle_search_books({"query": "Dune"})
    assert result["error"] is True
```

**Step 6: Run to verify failure**

```bash
pytest tests/mcp_servers/books/test_server.py -v
```
Expected: `ModuleNotFoundError`

**Step 7: Implement `mcp_servers/books/server.py`**

```python
import os
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from dotenv import load_dotenv
from mcp_servers.books.hardcover_client import HardcoverClient

load_dotenv()

app = Server("books-api")
_hardcover_client: HardcoverClient | None = None

def get_hardcover_client() -> HardcoverClient:
    global _hardcover_client
    if _hardcover_client is None:
        _hardcover_client = HardcoverClient(api_key=os.environ["HARDCOVER_API_KEY"])
    return _hardcover_client

async def handle_search_books(args: dict) -> list | dict:
    client = get_hardcover_client()
    return await client.search_books(args["query"])

async def handle_get_book_details(args: dict) -> dict:
    client = get_hardcover_client()
    return await client.get_book_details(int(args["book_id"]))

async def handle_get_book_reviews(args: dict) -> list | dict:
    client = get_hardcover_client()
    return await client.get_book_reviews(int(args["book_id"]), int(args.get("limit", 20)))

async def handle_search_reviews(args: dict) -> list | dict:
    """Search reviews by keyword across all books."""
    # Google Books supplemental search for review content
    query = args["query"]
    client = get_hardcover_client()
    books = await client.search_books(query)
    if isinstance(books, dict) and books.get("error"):
        return books
    results = []
    for book in books[:3]:
        reviews = await client.get_book_reviews(int(book["id"]), limit=5)
        if isinstance(reviews, list):
            for r in reviews:
                if query.lower() in str(r.get("review", "")).lower():
                    results.append({"book_title": book["title"], **r})
    return results

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_books",
            description="Search for books by title, author, ISBN, or genre. Returns a list of matching books with id, title, and author. Use this when you need to find books matching a query. Different from get_book_details which fetches full info for a known book id.",
            inputSchema={"type": "object", "properties": {"query": {"type": "string", "description": "Search query — title, author name, ISBN, or genre"}}, "required": ["query"]},
        ),
        types.Tool(
            name="get_book_details",
            description="Get full metadata for a specific book by its Hardcover book_id. Returns description, ratings, page count, genres, cover URL, release date. Use this after search_books to get complete details for a known book.",
            inputSchema={"type": "object", "properties": {"book_id": {"type": "string", "description": "Hardcover book ID (from search_books results)"}}, "required": ["book_id"]},
        ),
        types.Tool(
            name="get_book_reviews",
            description="Fetch all reviews for a specific book by its Hardcover book_id. Returns reviewer username, rating, and review text. Use this when you want all reviews for one specific book. Different from search_reviews which searches review text across multiple books.",
            inputSchema={"type": "object", "properties": {"book_id": {"type": "string"}, "limit": {"type": "integer", "default": 20}}, "required": ["book_id"]},
        ),
        types.Tool(
            name="search_reviews",
            description="Full-text search across reviews by keyword, topic, or sentiment (e.g. 'slow start', 'great worldbuilding'). Searches review content across multiple books. Different from get_book_reviews which fetches all reviews for a single specific book.",
            inputSchema={"type": "object", "properties": {"query": {"type": "string", "description": "Keyword, topic, or phrase to search for in review text"}}, "required": ["query"]},
        ),
        types.Tool(
            name="get_recommendations",
            description="Get book recommendations similar to a given title. Returns a list of recommended books with titles and authors.",
            inputSchema={"type": "object", "properties": {"title": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["title"]},
        ),
        types.Tool(
            name="get_author_details",
            description="Get author biography, full bibliography, and similar authors by author name.",
            inputSchema={"type": "object", "properties": {"author_name": {"type": "string"}}, "required": ["author_name"]},
        ),
        types.Tool(
            name="get_book_editions",
            description="Get all editions of a book (formats, languages, publishers) by Hardcover book_id.",
            inputSchema={"type": "object", "properties": {"book_id": {"type": "string"}}, "required": ["book_id"]},
        ),
        types.Tool(
            name="get_trending_books",
            description="Get currently trending or popular books, optionally filtered by genre.",
            inputSchema={"type": "object", "properties": {"genre": {"type": "string", "description": "Optional genre filter"}, "limit": {"type": "integer", "default": 10}}, "required": []},
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    import json
    handlers = {
        "search_books": handle_search_books,
        "get_book_details": handle_get_book_details,
        "get_book_reviews": handle_get_book_reviews,
        "search_reviews": handle_search_reviews,
    }
    handler = handlers.get(name)
    if not handler:
        result = {"error": True, "errorCategory": "validation", "isRetryable": False, "message": f"Unknown tool: {name}"}
    else:
        try:
            result = await handler(arguments)
        except Exception as e:
            result = {"error": True, "errorCategory": "transient", "isRetryable": False, "message": str(e)}
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

**Step 8: Run all books tests**

```bash
pytest tests/mcp_servers/books/ -v
```
Expected: All PASS

**Step 9: Commit**

```bash
git add mcp_servers/books/ tests/mcp_servers/books/
git commit -m "feat: MCP Server #1 — Books API (Hardcover client + 8 tools)"
```

---

## Task 4: MCP Server #2 — Databricks

**Files:**
- Create: `mcp_servers/databricks/server.py`
- Create: `mcp_servers/databricks/db_client.py`
- Create: `tests/mcp_servers/databricks/test_server.py`
- Create: `tests/mcp_servers/databricks/test_db_client.py`

**Step 1: Write failing tests**

```python
# tests/mcp_servers/databricks/test_db_client.py
import pytest
from unittest.mock import MagicMock, patch

def test_get_reading_stats_returns_structured_data():
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [("read", 12), ("reading", 2), ("want_to_read", 45)]
    mock_cursor.description = [("status",), ("count",)]
    with patch("mcp_servers.databricks.db_client.get_cursor", return_value=mock_cursor):
        from mcp_servers.databricks.db_client import get_reading_stats
        result = get_reading_stats()
    assert result["read"] == 12
    assert result["reading"] == 2

def test_query_reading_log_uses_parameterized_sql():
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_cursor.description = [("entry_id",), ("title",), ("status",)]
    with patch("mcp_servers.databricks.db_client.get_cursor", return_value=mock_cursor):
        from mcp_servers.databricks.db_client import query_reading_log
        query_reading_log(status="read")
    call_args = mock_cursor.execute.call_args
    # Ensure parameterized — status value should be in params, not the SQL string
    sql_str = call_args[0][0]
    assert "read" not in sql_str or "?" in sql_str or "%s" in sql_str
```

**Step 2: Run to verify failure**

```bash
pytest tests/mcp_servers/databricks/ -v
```
Expected: `ModuleNotFoundError`

**Step 3: Implement `mcp_servers/databricks/db_client.py`**

```python
import os
from databricks import sql
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()

def get_connection():
    return sql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"].replace("https://", ""),
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        access_token=os.environ["DATABRICKS_TOKEN"],
    )

@contextmanager
def get_cursor():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            yield cursor
    finally:
        conn.close()

def _rows_to_dicts(cursor) -> list[dict]:
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

def get_reading_stats() -> dict:
    with get_cursor() as cursor:
        cursor.execute("SELECT status, COUNT(*) as count FROM abip.reading.reading_log GROUP BY status")
        rows = _rows_to_dicts(cursor)
    return {r["status"]: r["count"] for r in rows}

def query_reading_log(status: str = None, limit: int = 50) -> list[dict]:
    with get_cursor() as cursor:
        if status:
            cursor.execute(
                "SELECT * FROM abip.reading.reading_log WHERE status = %s ORDER BY updated_at DESC LIMIT %s",
                (status, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM abip.reading.reading_log ORDER BY updated_at DESC LIMIT %s",
                (limit,)
            )
        return _rows_to_dicts(cursor)

def add_book_to_library(book_id: str, title: str, status: str) -> dict:
    import uuid
    from datetime import datetime
    entry_id = str(uuid.uuid4())
    with get_cursor() as cursor:
        cursor.execute(
            "INSERT INTO abip.reading.reading_log (entry_id, book_id, title, status) VALUES (%s, %s, %s, %s)",
            (entry_id, book_id, title, status)
        )
    return {"entry_id": entry_id, "book_id": book_id, "title": title, "status": status}

def update_reading_status(book_id: str, status: str, rating: int = None) -> dict:
    with get_cursor() as cursor:
        if rating is not None:
            cursor.execute(
                "UPDATE abip.reading.reading_log SET status = %s, rating = %s, updated_at = CURRENT_TIMESTAMP WHERE book_id = %s",
                (status, rating, book_id)
            )
        else:
            cursor.execute(
                "UPDATE abip.reading.reading_log SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE book_id = %s",
                (status, book_id)
            )
    return {"book_id": book_id, "status": status, "rating": rating}
```

**Step 4: Implement `mcp_servers/databricks/server.py`**

```python
import os
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from dotenv import load_dotenv

load_dotenv()
app = Server("databricks")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="query_reading_log",
            description="Query your personal reading history from Delta Lake. Filter by status (read, reading, want_to_read). Returns list of books with title, status, rating, and dates. Use for 'what have I read?' type questions.",
            inputSchema={"type": "object", "properties": {"status": {"type": "string", "enum": ["read", "reading", "want_to_read"]}, "limit": {"type": "integer", "default": 50}}, "required": []},
        ),
        types.Tool(
            name="get_reading_stats",
            description="Get aggregated reading statistics: total books by status, average rating, books per month, top genres. Use for 'how many books did I read?' or dashboard data.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="add_book_to_library",
            description="Add a new book to your personal reading library with a status (read, reading, want_to_read). Use after confirming book details with search_books.",
            inputSchema={"type": "object", "properties": {"book_id": {"type": "string"}, "title": {"type": "string"}, "status": {"type": "string", "enum": ["read", "reading", "want_to_read"]}}, "required": ["book_id", "title", "status"]},
        ),
        types.Tool(
            name="update_reading_status",
            description="Update the reading status and optionally rating for a book already in your library.",
            inputSchema={"type": "object", "properties": {"book_id": {"type": "string"}, "status": {"type": "string", "enum": ["read", "reading", "want_to_read"]}, "rating": {"type": "integer", "minimum": 1, "maximum": 5}}, "required": ["book_id", "status"]},
        ),
        types.Tool(
            name="search_my_library",
            description="Semantic vector search across your personal library using natural language. E.g. 'books about survival in space' or 'epic fantasy with magic systems'. Uses FM embeddings — different from query_reading_log which filters by exact status.",
            inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]},
        ),
        types.Tool(
            name="trigger_enrichment_job",
            description="Trigger the Databricks enrichment workflow to generate AI reading brief and embeddings for a specific book.",
            inputSchema={"type": "object", "properties": {"book_id": {"type": "string"}}, "required": ["book_id"]},
        ),
        types.Tool(
            name="get_job_status",
            description="Check the current status of a Databricks workflow job run by run_id.",
            inputSchema={"type": "object", "properties": {"run_id": {"type": "string"}}, "required": ["run_id"]},
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    from mcp_servers.databricks import db_client
    try:
        if name == "query_reading_log":
            result = db_client.query_reading_log(**arguments)
        elif name == "get_reading_stats":
            result = db_client.get_reading_stats()
        elif name == "add_book_to_library":
            result = db_client.add_book_to_library(**arguments)
        elif name == "update_reading_status":
            result = db_client.update_reading_status(**arguments)
        elif name == "trigger_enrichment_job":
            from mcp_servers.databricks.job_client import trigger_enrichment
            result = trigger_enrichment(arguments["book_id"])
        elif name == "get_job_status":
            from mcp_servers.databricks.job_client import get_job_status
            result = get_job_status(arguments["run_id"])
        elif name == "search_my_library":
            result = {"error": True, "errorCategory": "transient", "isRetryable": False, "message": "Vector search not yet implemented — requires FM index setup"}
        else:
            result = {"error": True, "errorCategory": "validation", "isRetryable": False, "message": f"Unknown tool: {name}"}
    except Exception as e:
        result = {"error": True, "errorCategory": "transient", "isRetryable": False, "message": str(e)}
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

**Step 5: Run all Databricks tests**

```bash
pytest tests/mcp_servers/databricks/ -v
```
Expected: All PASS

**Step 6: Commit**

```bash
git add mcp_servers/databricks/ tests/mcp_servers/databricks/
git commit -m "feat: MCP Server #2 — Databricks (Delta Lake queries + job triggers, 7 tools)"
```

---

## Task 5: MCP Server #3 — Annotations

**Files:**
- Create: `mcp_servers/annotations/server.py`
- Create: `mcp_servers/annotations/db.py`
- Create: `tests/mcp_servers/annotations/test_server.py`

**Step 1: Write failing tests**

```python
# tests/mcp_servers/annotations/test_server.py
import pytest
import sqlite3
import tempfile
import os

@pytest.fixture
def temp_db(tmp_path):
    db_path = str(tmp_path / "test_annotations.db")
    os.environ["ANNOTATIONS_DB_PATH"] = db_path
    return db_path

def test_add_and_get_annotation(temp_db):
    from mcp_servers.annotations.db import AnnotationsDB
    db = AnnotationsDB(temp_db)
    db.init_schema()
    annotation_id = db.add_annotation(book_id="book1", book_title="Dune", annotation_type="highlight", content="I must not fear.")
    results = db.get_annotations(book_id="book1")
    assert len(results) == 1
    assert results[0]["content"] == "I must not fear."

def test_search_annotations_finds_by_keyword(temp_db):
    from mcp_servers.annotations.db import AnnotationsDB
    db = AnnotationsDB(temp_db)
    db.init_schema()
    db.add_annotation(book_id="b1", book_title="Dune", annotation_type="note", content="Fear is the mind killer")
    db.add_annotation(book_id="b2", book_title="Foundation", annotation_type="note", content="The fall of the empire")
    results = db.search_annotations("fear")
    assert len(results) == 1
    assert "Dune" in results[0]["book_title"]
```

**Step 2: Run to verify failure**

```bash
pytest tests/mcp_servers/annotations/ -v
```
Expected: `ModuleNotFoundError`

**Step 3: Implement `mcp_servers/annotations/db.py`**

```python
import sqlite3
import uuid
from datetime import datetime

class AnnotationsDB:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def init_schema(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS annotations (
                    id TEXT PRIMARY KEY,
                    book_id TEXT NOT NULL,
                    book_title TEXT,
                    annotation_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    page_number INTEGER,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id TEXT PRIMARY KEY,
                    book_id TEXT NOT NULL,
                    book_title TEXT,
                    session_date TEXT NOT NULL,
                    content TEXT NOT NULL,
                    mood TEXT,
                    pages_read INTEGER,
                    created_at TEXT DEFAULT (datetime('now'))
                );
            """)

    def add_annotation(self, book_id: str, book_title: str, annotation_type: str, content: str, page_number: int = None) -> str:
        annotation_id = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO annotations (id, book_id, book_title, annotation_type, content, page_number) VALUES (?,?,?,?,?,?)",
                (annotation_id, book_id, book_title, annotation_type, content, page_number)
            )
        return annotation_id

    def get_annotations(self, book_id: str = None) -> list[dict]:
        with self._conn() as conn:
            if book_id:
                rows = conn.execute("SELECT * FROM annotations WHERE book_id = ? ORDER BY created_at DESC", (book_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM annotations ORDER BY created_at DESC").fetchall()
            cols = ["id", "book_id", "book_title", "annotation_type", "content", "page_number", "created_at"]
            return [dict(zip(cols, r)) for r in rows]

    def search_annotations(self, query: str) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM annotations WHERE content LIKE ? OR book_title LIKE ? ORDER BY created_at DESC",
                (f"%{query}%", f"%{query}%")
            ).fetchall()
            cols = ["id", "book_id", "book_title", "annotation_type", "content", "page_number", "created_at"]
            return [dict(zip(cols, r)) for r in rows]

    def add_journal_entry(self, book_id: str, book_title: str, session_date: str, content: str, mood: str = None, pages_read: int = None) -> str:
        entry_id = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO journal_entries (id, book_id, book_title, session_date, content, mood, pages_read) VALUES (?,?,?,?,?,?,?)",
                (entry_id, book_id, book_title, session_date, content, mood, pages_read)
            )
        return entry_id

    def get_journal_entries(self, book_id: str = None) -> list[dict]:
        with self._conn() as conn:
            if book_id:
                rows = conn.execute("SELECT * FROM journal_entries WHERE book_id = ? ORDER BY session_date DESC", (book_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM journal_entries ORDER BY session_date DESC").fetchall()
            cols = ["id", "book_id", "book_title", "session_date", "content", "mood", "pages_read", "created_at"]
            return [dict(zip(cols, r)) for r in rows]
```

**Step 4: Implement `mcp_servers/annotations/server.py`**

```python
import os
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from dotenv import load_dotenv
from mcp_servers.annotations.db import AnnotationsDB

load_dotenv()
app = Server("annotations")

def get_db() -> AnnotationsDB:
    db_path = os.environ.get("ANNOTATIONS_DB_PATH", "data/annotations.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db = AnnotationsDB(db_path)
    db.init_schema()
    return db

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(name="add_annotation", description="Save a highlight, note, or quote from a book with optional page number.", inputSchema={"type": "object", "properties": {"book_id": {"type": "string"}, "book_title": {"type": "string"}, "annotation_type": {"type": "string", "enum": ["highlight", "note", "quote"]}, "content": {"type": "string"}, "page_number": {"type": "integer"}}, "required": ["book_id", "book_title", "annotation_type", "content"]}),
        types.Tool(name="get_annotations", description="Retrieve all annotations for a specific book_id, or all annotations if no book_id provided.", inputSchema={"type": "object", "properties": {"book_id": {"type": "string"}}, "required": []}),
        types.Tool(name="search_annotations", description="Full-text search across all annotations and journal entries by keyword.", inputSchema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}),
        types.Tool(name="add_journal_entry", description="Log a reading session with date, thoughts, mood, and pages read.", inputSchema={"type": "object", "properties": {"book_id": {"type": "string"}, "book_title": {"type": "string"}, "session_date": {"type": "string", "description": "ISO date YYYY-MM-DD"}, "content": {"type": "string"}, "mood": {"type": "string"}, "pages_read": {"type": "integer"}}, "required": ["book_id", "book_title", "session_date", "content"]}),
        types.Tool(name="get_journal_entries", description="Retrieve reading journal entries for a specific book or all entries.", inputSchema={"type": "object", "properties": {"book_id": {"type": "string"}}, "required": []}),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        db = get_db()
        if name == "add_annotation":
            result = {"id": db.add_annotation(**arguments)}
        elif name == "get_annotations":
            result = db.get_annotations(**arguments)
        elif name == "search_annotations":
            result = db.search_annotations(arguments["query"])
        elif name == "add_journal_entry":
            result = {"id": db.add_journal_entry(**arguments)}
        elif name == "get_journal_entries":
            result = db.get_journal_entries(**arguments)
        else:
            result = {"error": True, "errorCategory": "validation", "isRetryable": False, "message": f"Unknown tool: {name}"}
    except Exception as e:
        result = {"error": True, "errorCategory": "transient", "isRetryable": False, "message": str(e)}
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

**Step 5: Run all annotations tests**

```bash
pytest tests/mcp_servers/annotations/ -v
```
Expected: All PASS

**Step 6: Commit**

```bash
git add mcp_servers/annotations/ tests/mcp_servers/annotations/
git commit -m "feat: MCP Server #3 — Annotations (SQLite, 5 tools, journal + highlights)"
```

---

## Task 6: Multi-Agent System — Base + Hooks

**Files:**
- Create: `agents/hooks.py`
- Create: `agents/base.py`
- Create: `tests/agents/test_hooks.py`

**Step 1: Write failing tests for hooks**

```python
# tests/agents/test_hooks.py
import pytest
from agents.hooks import normalize_timestamps, audit_log_hook

def test_normalize_unix_timestamp():
    tool_result = {"created_at": 1700000000, "title": "Dune"}
    normalized = normalize_timestamps(tool_result)
    assert "T" in normalized["created_at"]  # ISO 8601 format
    assert normalized["title"] == "Dune"

def test_normalize_iso_timestamp_unchanged():
    tool_result = {"created_at": "2024-01-15T10:30:00Z", "title": "Dune"}
    normalized = normalize_timestamps(tool_result)
    assert normalized["created_at"] == "2024-01-15T10:30:00Z"

def test_normalize_handles_non_timestamp_int():
    tool_result = {"page_count": 412, "title": "Dune"}
    normalized = normalize_timestamps(tool_result)
    assert normalized["page_count"] == 412
```

**Step 2: Run to verify failure**

```bash
pytest tests/agents/test_hooks.py -v
```
Expected: `ModuleNotFoundError`

**Step 3: Implement `agents/hooks.py`**

```python
import json
import re
from datetime import datetime, timezone
from typing import Any

# Unix timestamps are typically 10 digits (seconds since epoch, year 2001-2286)
_UNIX_TS_RE = re.compile(r"^1[0-9]{9}$")

def normalize_timestamps(obj: Any) -> Any:
    """Recursively normalize Unix timestamps to ISO 8601 strings."""
    if isinstance(obj, dict):
        return {k: normalize_timestamps(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize_timestamps(item) for item in obj]
    if isinstance(obj, int) and _UNIX_TS_RE.match(str(obj)):
        return datetime.fromtimestamp(obj, tz=timezone.utc).isoformat()
    return obj

def post_tool_use_normalize(tool_name: str, tool_result: Any, read_only: bool = False) -> Any:
    """PostToolUse hook: normalize timestamps from all MCP tool results."""
    if isinstance(tool_result, (dict, list)):
        return normalize_timestamps(tool_result)
    return tool_result

def pre_tool_use_read_only(tool_name: str, tool_input: dict, read_only: bool = False) -> dict | None:
    """PreToolUse hook: block write operations in read-only mode.
    Returns None to allow, or an error dict to block.
    """
    WRITE_TOOLS = {"add_book_to_library", "update_reading_status", "add_annotation", "add_journal_entry", "trigger_enrichment_job"}
    if read_only and tool_name in WRITE_TOOLS:
        return {"blocked": True, "reason": f"Tool '{tool_name}' is blocked in read-only mode."}
    return None

def audit_log_hook(session_id: str, tool_name: str, tool_input: Any, tool_result: Any) -> None:
    """PostToolUse hook: write audit entry. In production, writes to abip.intelligence.audit_log."""
    import uuid
    entry = {
        "log_id": str(uuid.uuid4()),
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_input": json.dumps(tool_input),
        "tool_result": json.dumps(tool_result)[:2000],  # truncate large results
    }
    # TODO: write to Delta table in production; print for now
    print(f"[AUDIT] {entry['tool_name']} called in session {session_id[:8]}")
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/agents/test_hooks.py -v
```
Expected: All PASS

**Step 5: Commit**

```bash
git add agents/hooks.py agents/base.py tests/agents/test_hooks.py
git commit -m "feat: agent hooks — PostToolUse timestamp normalization, PreToolUse read-only enforcement, audit logging"
```

---

## Task 7: Coordinator + Subagents

**Files:**
- Create: `agents/coordinator.py`
- Create: `agents/book_discovery_agent.py`
- Create: `agents/data_intelligence_agent.py`
- Create: `agents/synthesis_agent.py`
- Create: `tests/agents/test_coordinator.py`

**Step 1: Write failing test for coordinator routing**

```python
# tests/agents/test_coordinator.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_coordinator_routes_stats_query_to_data_agent_only():
    """A 'how many books did I read?' query should only invoke the Data Intelligence agent."""
    with patch("agents.coordinator.run_data_intelligence_agent", new_callable=AsyncMock) as mock_data, \
         patch("agents.coordinator.run_book_discovery_agent", new_callable=AsyncMock) as mock_books, \
         patch("agents.coordinator.run_synthesis_agent", new_callable=AsyncMock) as mock_synth:
        mock_data.return_value = {"stats": {"read": 42}}
        mock_synth.return_value = "You've read 42 books!"
        from agents.coordinator import route_request
        result = await route_request("How many books did I read this year?")
    mock_data.assert_called_once()
    mock_books.assert_not_called()

@pytest.mark.asyncio
async def test_coordinator_routes_recommendation_to_multiple_agents():
    """A 'what should I read next?' query should invoke both book discovery and data intelligence."""
    with patch("agents.coordinator.run_data_intelligence_agent", new_callable=AsyncMock) as mock_data, \
         patch("agents.coordinator.run_book_discovery_agent", new_callable=AsyncMock) as mock_books, \
         patch("agents.coordinator.run_synthesis_agent", new_callable=AsyncMock) as mock_synth:
        mock_data.return_value = {"reading_history": []}
        mock_books.return_value = {"recommendations": []}
        mock_synth.return_value = "Here are my recommendations..."
        from agents.coordinator import route_request
        result = await route_request("What should I read next?")
    mock_data.assert_called_once()
    mock_books.assert_called_once()
    mock_synth.assert_called_once()
```

**Step 2: Run to verify failure**

```bash
pytest tests/agents/test_coordinator.py -v
```
Expected: `ModuleNotFoundError`

**Step 3: Implement `agents/book_discovery_agent.py`**

```python
import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You are the Book Discovery Agent. Your role is to search for books, fetch metadata, retrieve reviews, and find recommendations using the books MCP server tools.

Always return structured findings with source attribution: include book title, Hardcover book ID, and which API provided the data.
When searching reviews, clearly distinguish between get_book_reviews (all reviews for one book) and search_reviews (keyword search across reviews).
Return your findings as a JSON object with keys: books, reviews, recommendations, authors as appropriate."""

async def run_book_discovery_agent(task: str, mcp_tools: list) -> dict:
    """Run the Book Discovery subagent with explicit task context."""
    messages = [{"role": "user", "content": task}]
    book_tools = [t for t in mcp_tools if t["name"] in {
        "search_books", "get_book_details", "get_book_editions",
        "get_author_details", "get_recommendations", "get_trending_books",
        "get_book_reviews", "search_reviews"
    }]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=book_tools,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    try:
                        return json.loads(block.text)
                    except json.JSONDecodeError:
                        return {"raw_findings": block.text}
            return {}

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    from agents.hooks import post_tool_use_normalize
                    # Execute tool via MCP (placeholder — real impl uses MCP client)
                    raw_result = {"error": True, "message": "MCP client not connected in test"}
                    normalized = post_tool_use_normalize(block.name, raw_result)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(normalized),
                    })
            messages.append({"role": "user", "content": tool_results})
```

**Step 4: Implement `agents/data_intelligence_agent.py`** (same pattern, scoped to Databricks tools)

```python
import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You are the Data Intelligence Agent. Your role is to query reading history, fetch statistics, and manage the personal book library using the Databricks MCP server tools.

Return structured data results. For statistics, include the raw numbers and a brief interpretation.
Never fabricate data — if a query returns empty results, report that clearly."""

async def run_data_intelligence_agent(task: str, mcp_tools: list) -> dict:
    messages = [{"role": "user", "content": task}]
    db_tools = [t for t in mcp_tools if t["name"] in {
        "query_reading_log", "get_reading_stats", "search_my_library",
        "add_book_to_library", "update_reading_status", "trigger_enrichment_job", "get_job_status"
    }]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=db_tools,
            messages=messages,
        )
        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    try:
                        return json.loads(block.text)
                    except json.JSONDecodeError:
                        return {"raw_findings": block.text}
            return {}
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    from agents.hooks import post_tool_use_normalize
                    raw_result = {"error": True, "message": "MCP client not connected in test"}
                    normalized = post_tool_use_normalize(block.name, raw_result)
                    tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(normalized)})
            messages.append({"role": "user", "content": tool_results})
```

**Step 5: Implement `agents/synthesis_agent.py`**

```python
import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

FEW_SHOT_EXAMPLES = """
Example 1 — Recommendation response:
Input: {books_found: ["Project Hail Mary", "The Martian"], reading_history: {genres: ["sci-fi", "thriller"], avg_rating: 4.2}}
Output: "Based on your love of hard science fiction (you've rated sci-fi books 4.2/5 on average), I'd start with Project Hail Mary by Andy Weir — it combines the same problem-solving energy you enjoyed in The Martian with a deeply moving story about humanity's survival."

Example 2 — Reading brief:
Input: {book: "Dune", author: "Frank Herbert", description: "...", reviews: [...]}
Output: "Dune (1965) by Frank Herbert is foundational science fiction set on the desert planet Arrakis. Themes: ecological systems, religion as political tool, the dangers of messianic figures. Readers consistently praise the worldbuilding depth while noting the dense exposition in the first 100 pages requires patience."
"""

SYSTEM_PROMPT = f"""You are the Synthesis Agent. Your role is to combine findings from other agents into clear, helpful, personalized responses for the user.

You have access to the annotations tools to save and retrieve personal notes.

{FEW_SHOT_EXAMPLES}

Guidelines:
- Be specific and personalized — reference the user's actual reading history when available
- For recommendations, explain WHY based on their history
- For reading briefs, include themes, what readers love, and honest caveats
- Cite sources (which API, which agent provided data)"""

async def run_synthesis_agent(task: str, context: dict, mcp_tools: list) -> str:
    context_str = json.dumps(context, indent=2)
    user_message = f"Task: {task}\n\nContext from other agents:\n{context_str}"
    messages = [{"role": "user", "content": user_message}]
    annotation_tools = [t for t in mcp_tools if t["name"] in {
        "add_annotation", "get_annotations", "search_annotations",
        "add_journal_entry", "get_journal_entries", "verify_fact"
    }]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=annotation_tools if annotation_tools else [],
            messages=messages,
        )
        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    raw_result = {"error": True, "message": "MCP client not connected in test"}
                    tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(raw_result)})
            messages.append({"role": "user", "content": tool_results})
```

**Step 6: Implement `agents/coordinator.py`**

```python
import os
import asyncio
import json
import anthropic
from dotenv import load_dotenv
from agents.book_discovery_agent import run_book_discovery_agent
from agents.data_intelligence_agent import run_data_intelligence_agent
from agents.synthesis_agent import run_synthesis_agent

load_dotenv()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

ROUTING_SYSTEM_PROMPT = """You are the coordinator for a book intelligence platform. Given a user request, output a JSON routing plan.

Routing rules:
- "how many books", "reading stats", "my library data", "reading history" → data_only
- "find books", "reviews of", "author of", "what is X about" → books_only  
- "recommend", "what should I read", "reading brief", "tell me about" → all_agents
- "add to my list", "mark as read", "rate this book" → data_only

Output format: {"agents": ["book_discovery", "data_intelligence", "synthesis"], "book_task": "...", "data_task": "...", "synthesis_task": "..."}
Only include agents that are needed. Always include synthesis if multiple agents are used."""

async def route_request(user_message: str, mcp_tools: list = None, read_only: bool = False) -> str:
    if mcp_tools is None:
        mcp_tools = []

    # Step 1: Determine routing
    routing_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=ROUTING_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    try:
        routing = json.loads(routing_response.content[0].text)
    except (json.JSONDecodeError, IndexError, AttributeError):
        routing = {"agents": ["book_discovery", "data_intelligence", "synthesis"],
                   "book_task": user_message, "data_task": user_message, "synthesis_task": user_message}

    agents_to_run = routing.get("agents", [])
    context = {}

    # Step 2: Run independent agents in parallel
    parallel_tasks = []
    if "book_discovery" in agents_to_run:
        parallel_tasks.append(("books", run_book_discovery_agent(routing.get("book_task", user_message), mcp_tools)))
    if "data_intelligence" in agents_to_run:
        parallel_tasks.append(("data", run_data_intelligence_agent(routing.get("data_task", user_message), mcp_tools)))

    if parallel_tasks:
        results = await asyncio.gather(*[task for _, task in parallel_tasks])
        for (key, _), result in zip(parallel_tasks, results):
            context[key] = result

    # Step 3: Synthesis (sequential — depends on above results)
    if "synthesis" in agents_to_run or (not parallel_tasks):
        return await run_synthesis_agent(routing.get("synthesis_task", user_message), context, mcp_tools)

    # If only one agent, return its result directly
    return json.dumps(context, indent=2)
```

**Step 7: Run all agent tests**

```bash
pytest tests/agents/ -v
```
Expected: All PASS

**Step 8: Commit**

```bash
git add agents/ tests/agents/
git commit -m "feat: multi-agent system — coordinator routing + 3 subagents with scoped tool access + hooks"
```

---

## Task 8: Streamlit App

**Files:**
- Create: `app/main.py`
- Create: `app/pages/1_Chat.py`
- Create: `app/pages/2_My_Library.py`
- Create: `app/pages/3_Discover.py`
- Create: `app/pages/4_Insights.py`
- Create: `app/pages/5_Annotations.py`
- Create: `app/utils.py`

**Step 1: Implement `app/utils.py`**

```python
import os
import asyncio
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_agent_response(user_message: str) -> str:
    """Call the coordinator agent and return response."""
    from agents.coordinator import route_request
    return asyncio.run(route_request(user_message, mcp_tools=[]))

def init_chat_history():
    if "messages" not in st.session_state:
        st.session_state.messages = []

def add_message(role: str, content: str):
    st.session_state.messages.append({"role": role, "content": content})
```

**Step 2: Implement `app/main.py`**

```python
import streamlit as st

st.set_page_config(
    page_title="Agentic Book Intelligence Platform",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Agentic Book Intelligence Platform")
st.write("Welcome! Use the sidebar to navigate between Chat, Library, Discover, Insights, and Annotations.")
st.info("Ask anything in Chat — 'What should I read next?', 'How many books did I finish this year?', 'Tell me about the Mistborn series'")
```

**Step 3: Implement `app/pages/1_Chat.py`**

```python
import streamlit as st
from app.utils import get_agent_response, init_chat_history, add_message

st.title("Chat with your Book Intelligence")
init_chat_history()

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Tool activity sidebar
with st.sidebar:
    st.subheader("Agent Activity")
    if st.session_state.get("last_agents_used"):
        for agent in st.session_state.last_agents_used:
            st.write(f"- {agent}")

# Input
if prompt := st.chat_input("Ask about books, your reading history, or get recommendations..."):
    add_message("user", prompt)
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_agent_response(prompt)
        st.write(response)
    add_message("assistant", response)
```

**Step 4: Implement `app/pages/4_Insights.py`** (dashboard page — most complex)

```python
import streamlit as st
import plotly.express as px
import pandas as pd

st.title("Reading Insights")

try:
    from mcp_servers.databricks.db_client import get_reading_stats, query_reading_log
    stats = get_reading_stats()
    log = query_reading_log()

    col1, col2, col3 = st.columns(3)
    col1.metric("Books Read", stats.get("read", 0))
    col2.metric("Currently Reading", stats.get("reading", 0))
    col3.metric("Want to Read", stats.get("want_to_read", 0))

    if log:
        df = pd.DataFrame(log)
        if "finished_date" in df.columns and df["finished_date"].notna().any():
            df["month"] = pd.to_datetime(df["finished_date"], errors="coerce").dt.to_period("M").astype(str)
            monthly = df.groupby("month").size().reset_index(name="books_finished")
            st.subheader("Reading Velocity")
            fig = px.bar(monthly, x="month", y="books_finished", title="Books Finished per Month")
            st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.warning(f"Could not load stats: {e}. Check Databricks connection.")
    st.info("Stats will appear here once your Databricks workspace is connected.")
```

**Step 5: Run the app locally**

```bash
streamlit run app/main.py
```
Expected: App opens at localhost:8501, all 5 pages visible in sidebar.

**Step 6: Commit**

```bash
git add app/
git commit -m "feat: Streamlit app — 5 pages (Chat, Library, Discover, Insights, Annotations)"
```

---

## Task 9: Databricks Workflows

**Files:**
- Create: `workflows/job_sync.py`
- Create: `workflows/job_enrichment.py`
- Create: `workflows/job_digest.py`
- Create: `tests/workflows/test_job_sync.py`

**Step 1: Write failing test for sync job**

```python
# tests/workflows/test_job_sync.py
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

@pytest.mark.asyncio
async def test_sync_job_upserts_books():
    mock_books = [{"id": "1", "title": "Dune", "author": "Frank Herbert"}]
    with patch("workflows.job_sync.fetch_new_books", new_callable=AsyncMock, return_value=mock_books) as mock_fetch, \
         patch("workflows.job_sync.upsert_books") as mock_upsert:
        from workflows.job_sync import run_sync
        await run_sync()
    mock_upsert.assert_called_once_with(mock_books)
```

**Step 2: Run to verify failure**

```bash
pytest tests/workflows/ -v
```

**Step 3: Implement `workflows/job_sync.py`**

```python
import os
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient

load_dotenv()

async def fetch_new_books() -> list[dict]:
    """Fetch books updated since last sync from Hardcover API."""
    from mcp_servers.books.hardcover_client import HardcoverClient
    client = HardcoverClient(api_key=os.environ["HARDCOVER_API_KEY"])
    results = await client.search_books("recent")  # In production: use date filter
    return results if isinstance(results, list) else []

def upsert_books(books: list[dict]) -> int:
    """Upsert books into abip.books.books Delta table."""
    from mcp_servers.databricks.db_client import get_cursor
    count = 0
    with get_cursor() as cursor:
        for book in books:
            cursor.execute("""
                MERGE INTO abip.books.books AS target
                USING (SELECT %s AS book_id, %s AS title, %s AS source) AS source
                ON target.book_id = source.book_id
                WHEN NOT MATCHED THEN INSERT (book_id, title, source) VALUES (source.book_id, source.title, source.source)
                WHEN MATCHED THEN UPDATE SET target.updated_at = CURRENT_TIMESTAMP
            """, (str(book.get("id", "")), book.get("title", ""), "hardcover"))
            count += 1
    return count

def queue_for_enrichment(book_ids: list[str]) -> None:
    """Add new books to the enrichment queue."""
    from mcp_servers.databricks.db_client import get_cursor
    with get_cursor() as cursor:
        for book_id in book_ids:
            cursor.execute(
                "INSERT INTO abip.books.enrichment_queue (book_id, status) VALUES (%s, 'pending') ON DUPLICATE KEY UPDATE status = status",
                (book_id,)
            )

async def run_sync():
    print(f"[{datetime.now()}] Starting nightly book sync...")
    books = await fetch_new_books()
    count = upsert_books(books)
    book_ids = [str(b.get("id", "")) for b in books]
    queue_for_enrichment(book_ids)
    print(f"[{datetime.now()}] Sync complete. {count} books upserted, {len(book_ids)} queued for enrichment.")

if __name__ == "__main__":
    asyncio.run(run_sync())
```

**Step 4: Implement `workflows/job_enrichment.py`**

```python
import os
import asyncio
import anthropic
from dotenv import load_dotenv

load_dotenv()

async def generate_reading_brief(book: dict) -> str:
    """Generate an AI reading brief for a book using Claude."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = f"""Generate a concise reading brief for this book:
Title: {book.get('title', 'Unknown')}
Description: {book.get('description', 'No description available')}

Include: themes, what readers love about it, one honest caveat, and a one-sentence recommendation for who should read it.
Keep it under 150 words."""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text

async def run_enrichment():
    """Process all books in the enrichment queue."""
    from mcp_servers.databricks.db_client import get_cursor
    with get_cursor() as cursor:
        cursor.execute("SELECT book_id FROM abip.books.enrichment_queue WHERE status = 'pending' LIMIT 50")
        pending = [row[0] for row in cursor.fetchall()]

    print(f"Enriching {len(pending)} books...")
    for book_id in pending:
        book = {"title": f"Book {book_id}", "description": ""}  # In production: fetch full details
        brief = await generate_reading_brief(book)
        with get_cursor() as cursor:
            cursor.execute(
                "MERGE INTO abip.intelligence.reading_briefs USING (SELECT %s AS book_id, %s AS brief_text) src ON target.book_id = src.book_id WHEN MATCHED THEN UPDATE SET target.brief_text = src.brief_text, target.generated_at = CURRENT_TIMESTAMP WHEN NOT MATCHED THEN INSERT (book_id, brief_text) VALUES (src.book_id, src.brief_text)",
                (book_id, brief)
            )
            cursor.execute("UPDATE abip.books.enrichment_queue SET status = 'done', processed_at = CURRENT_TIMESTAMP WHERE book_id = %s", (book_id,))
    print(f"Enrichment complete.")

if __name__ == "__main__":
    asyncio.run(run_enrichment())
```

**Step 5: Implement `workflows/job_digest.py`**

```python
import os
import asyncio
import anthropic
from dotenv import load_dotenv

load_dotenv()

async def run_digest():
    """Generate the weekly reading digest using Claude."""
    from mcp_servers.databricks.db_client import query_reading_log, get_reading_stats
    recent = query_reading_log(status="read")[:10]
    stats = get_reading_stats()

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = f"""Generate a personalized weekly reading digest.

Reading stats this week: {stats}
Recently finished books: {[b['title'] for b in recent[:5]]}

Write a warm, encouraging 2-3 paragraph digest that:
1. Celebrates their reading activity
2. Notes any interesting patterns (genres, pace)  
3. Suggests something for next week based on what they've read

Keep it personal and under 200 words."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    digest = response.content[0].text
    print(f"Weekly digest generated:\n{digest}")
    return digest

if __name__ == "__main__":
    asyncio.run(run_digest())
```

**Step 6: Run workflow tests**

```bash
pytest tests/workflows/ -v
```
Expected: All PASS

**Step 7: Commit**

```bash
git add workflows/ tests/workflows/
git commit -m "feat: Databricks Workflows — nightly sync, book enrichment pipeline, weekly digest"
```

---

## Task 10: CI/CD — GitHub Actions with Claude Code

**Files:**
- Create: `.github/workflows/claude-review.yml`
- Create: `.github/workflows/tests.yml`

**Step 1: Create `.github/workflows/tests.yml`**

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --ignore=tests/integration
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

**Step 2: Create `.github/workflows/claude-review.yml`**

```yaml
name: Claude Code Review

on:
  pull_request:
    branches: [main]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Install Claude Code
        run: npm install -g @anthropic-ai/claude-code

      - name: Run Claude Code Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          git diff origin/main...HEAD > /tmp/pr_diff.txt
          claude -p "Review this PR diff for the Agentic Book Intelligence Platform. Check for: 1) Structured error responses from MCP tools (must include errorCategory, isRetryable, message), 2) Parameterized SQL queries (no f-string SQL), 3) Missing type hints on function signatures, 4) Hardcoded API keys or secrets. Output JSON array: [{\"file\": \"...\", \"line\": N, \"severity\": \"error|warning\", \"issue\": \"...\", \"suggestion\": \"...\"}]. Only report genuine issues, not style preferences." \
            --output-format json \
            < /tmp/pr_diff.txt > /tmp/review.json

      - name: Post review comments
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = JSON.parse(fs.readFileSync('/tmp/review.json', 'utf8'));
            if (review.length === 0) {
              github.rest.issues.createComment({issue_number: context.issue.number, owner: context.repo.owner, repo: context.repo.repo, body: "Claude Code review: No issues found."});
            } else {
              const body = review.map(r => `**${r.severity.toUpperCase()}** \`${r.file}:${r.line}\`\n${r.issue}\n*Suggestion: ${r.suggestion}*`).join('\n\n');
              github.rest.issues.createComment({issue_number: context.issue.number, owner: context.repo.owner, repo: context.repo.repo, body: `## Claude Code Review\n\n${body}`});
            }
```

**Step 3: Commit**

```bash
mkdir -p .github/workflows
git add .github/
git commit -m "feat: CI/CD — GitHub Actions tests + Claude Code automated PR review"
```

---

## Phase 2 Addendum: Event-Driven Pipeline

> These tasks extend Phase 1 without modifying any existing code.

### Task 11: Delta Live Tables Enrichment Pipeline

**Files:**
- Create: `workflows/dlt_enrichment_pipeline.py`
- Create: `workflows/webhook_receiver.py`

**Step 1: Implement DLT pipeline notebook** (`workflows/dlt_enrichment_pipeline.py`)

```python
# Databricks DLT pipeline — deploy as a notebook in Databricks
import dlt
from pyspark.sql.functions import col

@dlt.table(comment="Books pending AI enrichment")
def enrichment_queue():
    return spark.table("abip.books.enrichment_queue").filter(col("status") == "pending")

@dlt.table(comment="AI-generated reading briefs")
def reading_briefs():
    pending = dlt.read("enrichment_queue")
    # In production: call enrichment agent via Databricks SDK for each row
    return pending.select("book_id")
```

**Step 2: Implement webhook receiver** (`workflows/webhook_receiver.py`)

```python
import os
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

@app.post("/webhook/hardcover")
async def hardcover_webhook(request: Request):
    """Receive new book events from Hardcover, queue for enrichment."""
    payload = await request.json()
    book_id = payload.get("book_id")
    if book_id:
        from mcp_servers.databricks.db_client import get_cursor
        with get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO abip.books.enrichment_queue (book_id, status) VALUES (%s, 'pending')",
                (book_id,)
            )
        return {"status": "queued", "book_id": book_id}
    return {"status": "ignored"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

**Step 3: Commit**

```bash
git add workflows/dlt_enrichment_pipeline.py workflows/webhook_receiver.py
git commit -m "feat(phase2): DLT enrichment pipeline + webhook receiver for event-driven agent triggers"
```

---

## Deployment Checklist

Before deploying to Databricks Apps:

- [ ] All environment variables set as Databricks secrets
- [ ] Unity Catalog schema created (`python workflows/setup_schema.py`)
- [ ] MCP servers tested locally (`python mcp_servers/books/server.py`)
- [ ] Streamlit app runs locally (`streamlit run app/main.py`)
- [ ] Databricks Workflows created for Jobs 1-3
- [ ] Vector Search index created on `abip.intelligence.book_embeddings`
- [ ] GitHub secrets set: `ANTHROPIC_API_KEY`
- [ ] `.env` file NOT committed (in `.gitignore`)
