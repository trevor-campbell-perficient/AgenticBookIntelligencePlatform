import asyncio
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


async def fetch_new_books() -> list[dict]:
    """Fetch books updated since last sync from Hardcover API."""
    import os
    from mcp_servers.books.hardcover_client import HardcoverClient
    client = HardcoverClient(api_key=os.environ.get("HARDCOVER_API_KEY", ""))
    results = await client.search_books("recent")
    return results if isinstance(results, list) else []


def upsert_books(books: list[dict]) -> list[dict]:
    """Upsert books into abip.books.books Delta table using MERGE INTO. Returns the upserted books."""
    from mcp_servers.databricks.db_client import get_cursor
    if not books:
        return books
    with get_cursor() as cursor:
        for book in books:
            cursor.execute(
                """MERGE INTO abip.books.books AS target
                   USING (SELECT %s AS book_id, %s AS title, %s AS source) AS source
                   ON target.book_id = source.book_id
                   WHEN NOT MATCHED THEN INSERT (book_id, title, source)
                       VALUES (source.book_id, source.title, source.source)
                   WHEN MATCHED THEN UPDATE SET target.updated_at = CURRENT_TIMESTAMP""",
                (str(book.get("id", "")), book.get("title", ""), "hardcover"),
            )
    return books


def queue_for_enrichment(book_ids: list[str]) -> None:
    """Add new books to the enrichment queue using MERGE INTO."""
    if not book_ids:
        return
    from mcp_servers.databricks.db_client import get_cursor
    with get_cursor() as cursor:
        for book_id in book_ids:
            cursor.execute(
                """MERGE INTO abip.books.enrichment_queue AS target
                   USING (SELECT %s AS book_id) AS source
                   ON target.book_id = source.book_id
                   WHEN NOT MATCHED THEN INSERT (book_id, status) VALUES (source.book_id, 'pending')""",
                (book_id,),
            )


async def run_sync() -> None:
    """Run the nightly book sync job."""
    print(f"[{datetime.now().isoformat()}] Starting nightly book sync...")
    books = await fetch_new_books()
    upserted = upsert_books(books)
    book_ids = [str(b.get("id", "")) for b in upserted]
    queue_for_enrichment(book_ids)
    print(f"[{datetime.now().isoformat()}] Sync complete. {len(book_ids)} books upserted, {len(book_ids)} queued for enrichment.")


if __name__ == "__main__":
    asyncio.run(run_sync())
