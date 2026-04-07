import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


async def fetch_new_books() -> list[dict]:
    """Fetch books updated since last sync from Hardcover API."""
    import os
    from mcp_servers.books.hardcover_client import HardcoverClient
    client = HardcoverClient(api_key=os.environ.get("HARDCOVER_API_KEY", ""))
    results = await client.search_books("recent")
    return results if isinstance(results, list) else []


def upsert_books(books: list[dict]) -> int:
    """Upsert books into abip.books.books Delta table using MERGE INTO. Returns count of upserted books."""
    from mcp_servers.databricks.db_client import get_cursor
    if not books:
        return 0
    count = 0
    with get_cursor() as cursor:
        for book in books:
            cursor.execute(
                """MERGE INTO abip.books.books AS target
                   USING (SELECT ? AS book_id, ? AS title, ? AS source) AS source
                   ON target.book_id = source.book_id
                   WHEN MATCHED THEN UPDATE SET target.updated_at = CURRENT_TIMESTAMP
                   WHEN NOT MATCHED THEN INSERT (book_id, title, source)
                       VALUES (source.book_id, source.title, source.source)""",
                (str(book.get("id", "")), book.get("title", ""), "hardcover"),
            )
            count += 1
    return count


def queue_for_enrichment(book_ids: list[str]) -> None:
    """Add new books to the enrichment queue using MERGE INTO."""
    if not book_ids:
        return
    from mcp_servers.databricks.db_client import get_cursor
    with get_cursor() as cursor:
        for book_id in book_ids:
            cursor.execute(
                """MERGE INTO abip.books.enrichment_queue AS target
                   USING (SELECT ? AS book_id) AS source
                   ON target.book_id = source.book_id
                   WHEN MATCHED THEN UPDATE SET target.status = target.status
                   WHEN NOT MATCHED THEN INSERT (book_id, status) VALUES (source.book_id, 'pending')""",
                (book_id,),
            )


async def run_sync() -> None:
    """Run the nightly book sync job."""
    print(f"[{datetime.now().isoformat()}] Starting nightly book sync...")
    try:
        books = await fetch_new_books()
    except Exception as e:
        print(f"[ERROR] fetch_new_books failed: {e}")
        return
    try:
        count = upsert_books(books)
    except Exception as e:
        print(f"[ERROR] upsert_books failed: {e}")
        return
    book_ids = [str(b.get("id", "")) for b in books]
    try:
        queue_for_enrichment(book_ids)
    except Exception as e:
        print(f"[ERROR] queue_for_enrichment failed: {e}")
        return
    print(f"[{datetime.now().isoformat()}] Sync complete. {count} books upserted, {len(book_ids)} queued for enrichment.")


if __name__ == "__main__":
    asyncio.run(run_sync())
