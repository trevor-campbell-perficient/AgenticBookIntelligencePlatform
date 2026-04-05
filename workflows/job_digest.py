import asyncio
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

_client = None


def _get_client():
    global _client
    if _client is None:
        from agents.base import get_anthropic_client
        _client = get_anthropic_client()
    return _client


async def run_digest() -> str:
    """Generate the weekly reading digest using Claude."""
    from mcp_servers.databricks.db_client import query_reading_log, get_reading_stats
    recent = query_reading_log(status="read")[:10]
    stats = get_reading_stats()

    client = _get_client()
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
