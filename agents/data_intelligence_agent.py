import json
from typing import Any

from agents.hooks import post_tool_use_normalize

_client = None

def _get_client():
    global _client
    if _client is None:
        from agents.base import get_anthropic_client
        _client = get_anthropic_client()
    return _client

SYSTEM_PROMPT = """You are the Data Intelligence Agent. Your role is to query reading history, fetch statistics, and manage the personal book library using the Databricks MCP server tools.

Return structured data results. For statistics, include the raw numbers and a brief interpretation.
Never fabricate data — if a query returns empty results, report that clearly."""

SCOPED_TOOLS: frozenset[str] = frozenset({
    "query_reading_log", "get_reading_stats", "search_my_library",
    "add_book_to_library", "update_reading_status", "trigger_enrichment_job", "get_job_status"
})

async def run_data_intelligence_agent(task: str, mcp_tools: list) -> dict:
    client = _get_client()
    messages = [{"role": "user", "content": task}]
    db_tools = [t for t in mcp_tools if t["name"] in SCOPED_TOOLS]

    MAX_ITERATIONS = 10
    for _iteration in range(MAX_ITERATIONS):
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
                    raw_result = {"error": True, "message": "MCP client not connected in test"}
                    normalized = post_tool_use_normalize(block.name, raw_result)
                    tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(normalized)})
            messages.append({"role": "user", "content": tool_results})
        else:
            # Unexpected stop_reason — treat as terminal
            break

    return {}
