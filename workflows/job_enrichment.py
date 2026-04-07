import asyncio
from typing import Any
from dotenv import load_dotenv
from mcp_servers.databricks.db_client import get_cursor

load_dotenv()

_client = None


def _get_client() -> Any:
    global _client
    if _client is None:
        from agents.base import get_anthropic_client
        _client = get_anthropic_client()
    return _client


async def generate_reading_brief(book: dict) -> str:
    """Generate an AI reading brief for a book using Claude."""
    client = _get_client()
    prompt = (
        f"Generate a concise reading brief for this book:\n"
        f"Title: {book.get('title', 'Unknown')}\n"
        f"Description: {book.get('description', 'No description available')}\n\n"
        "Include: themes, what readers love about it, one honest caveat, and a one-sentence "
        "recommendation for who should read it. Keep it under 150 words."
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


async def run_enrichment() -> None:
    """Process all books in the enrichment queue."""
    with get_cursor() as cursor:
        cursor.execute(
            "SELECT book_id FROM abip.books.enrichment_queue WHERE status = 'pending' LIMIT 50"
        )
        pending = [row[0] for row in cursor.fetchall()]

    print(f"Enriching {len(pending)} books...")
    for book_id in pending:
        try:
            # Fetch real book data from Delta table
            with get_cursor() as cursor:
                cursor.execute(
                    "SELECT title, description FROM abip.books.books WHERE book_id = ?",
                    (book_id,),
                )
                row = cursor.fetchone()
            book = {"title": row[0] if row else f"Book {book_id}", "description": row[1] if row and row[1] else ""}
            brief = await generate_reading_brief(book)
            with get_cursor() as cursor:
                cursor.execute(
                    """MERGE INTO abip.intelligence.reading_briefs AS target
                       USING (SELECT ? AS book_id, ? AS brief_text) AS src
                       ON target.book_id = src.book_id
                       WHEN MATCHED THEN UPDATE SET target.brief_text = src.brief_text, target.generated_at = CURRENT_TIMESTAMP
                       WHEN NOT MATCHED THEN INSERT (book_id, brief_text, generated_at) VALUES (src.book_id, src.brief_text, CURRENT_TIMESTAMP)""",
                    (book_id, brief),
                )
                cursor.execute(
                    "UPDATE abip.books.enrichment_queue SET status = 'done', processed_at = CURRENT_TIMESTAMP WHERE book_id = ?",
                    (book_id,),
                )
            print(f"Enriched book_id={book_id}")
        except Exception as e:
            print(f"[ERROR] Failed to enrich book_id={book_id}: {e}")
            # Continue to next book — don't abort the batch
    print("Enrichment complete.")


if __name__ == "__main__":
    asyncio.run(run_enrichment())
