import json
from typing import Any

from agents.base import DEFAULT_MODEL
from agents.hooks import post_tool_use_normalize

_client = None

def _get_client():
    global _client
    if _client is None:
        from agents.base import get_anthropic_client, DEFAULT_MODEL
        _client = get_anthropic_client()
    return _client

SYSTEM_PROMPT = """You are the Book Discovery Agent. Your role is to search for books, fetch metadata, retrieve reviews, and find recommendations using the books MCP server tools.

Always return structured findings with source attribution: include book title, Hardcover book ID, and which API provided the data.
When searching reviews, clearly distinguish between get_book_reviews (all reviews for one book) and search_reviews (keyword search across reviews).
Return your findings as a JSON object with keys: books, reviews, recommendations, authors as appropriate."""

SCOPED_TOOLS: frozenset[str] = frozenset({
    "search_books", "get_book_details", "get_book_editions",
    "get_author_details", "get_recommendations", "get_trending_books",
    "get_book_reviews", "search_reviews"
})

async def run_book_discovery_agent(task: str, mcp_tools: list, tool_executor: Any = None) -> dict:
    """Run the Book Discovery subagent with explicit task context."""
    client = _get_client()
    messages = [{"role": "user", "content": task}]
    book_tools = [t for t in mcp_tools if t["name"] in SCOPED_TOOLS]

    MAX_ITERATIONS = 10
    for _iteration in range(MAX_ITERATIONS):
        response = client.messages.create(
            model=DEFAULT_MODEL,
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
                    if tool_executor is not None:
                        try:
                            raw_result = await tool_executor(block.name, block.input)
                        except Exception as e:
                            raw_result = {"error": True, "errorCategory": "transient", "isRetryable": True, "message": str(e)}
                    else:
                        raw_result = {"error": True, "errorCategory": "validation", "isRetryable": False, "message": "No tool executor provided"}
                    normalized = post_tool_use_normalize(block.name, raw_result)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(normalized),
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    return {}
