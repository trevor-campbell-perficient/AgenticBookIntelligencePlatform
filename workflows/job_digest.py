import asyncio
import uuid
from datetime import date, datetime
from typing import Any
from dotenv import load_dotenv
from mcp_servers.databricks.db_client import query_reading_log, get_reading_stats, get_cursor

load_dotenv()

_client = None


def _get_client() -> Any:
    global _client
    if _client is None:
        from agents.base import get_anthropic_client
        _client = get_anthropic_client()
    return _client


async def run_digest() -> str:
    """Generate the weekly reading digest using Claude."""
    try:
        recent = query_reading_log(status="read")[:10]
        stats = get_reading_stats()
    except Exception as e:
        print(f"[ERROR] Could not load reading data: {e}")
        return ""

    prompt = (
        "Generate a personalized weekly reading digest.\n\n"
        f"Reading stats this week: {stats}\n"
        f"Recently finished books: {[b['title'] for b in recent[:5]]}\n\n"
        "Write a warm, encouraging 2-3 paragraph digest that:\n"
        "1. Celebrates their reading activity\n"
        "2. Notes any interesting patterns (genres, pace)\n"
        "3. Suggests something for next week based on what they've read\n\n"
        "Keep it personal and under 200 words."
    )
    try:
        client = _get_client()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        digest = response.content[0].text
    except Exception as e:
        print(f"[ERROR] Claude API call failed: {e}")
        return ""

    print(f"Weekly digest generated:\n{digest}")

    try:
        digest_id = str(uuid.uuid4())
        with get_cursor() as cursor:
            cursor.execute(
                """MERGE INTO abip.intelligence.weekly_digests AS target
                   USING (SELECT %s AS digest_id, %s AS week_of, %s AS content) AS src
                   ON target.week_of = src.week_of
                   WHEN NOT MATCHED THEN INSERT (digest_id, week_of, content)
                       VALUES (src.digest_id, src.week_of, src.content)
                   WHEN MATCHED THEN UPDATE SET target.content = src.content,
                       target.generated_at = CURRENT_TIMESTAMP""",
                (digest_id, date.today().isoformat(), digest),
            )
        print(f"Digest saved to abip.intelligence.weekly_digests")
    except Exception as e:
        print(f"[WARNING] Could not persist digest to Delta: {e}")
        # Don't fail — return the digest even if persistence fails

    return digest


if __name__ == "__main__":
    asyncio.run(run_digest())
