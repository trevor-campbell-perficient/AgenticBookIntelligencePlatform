import asyncio
import json
from typing import Optional

from agents.book_discovery_agent import run_book_discovery_agent
from agents.data_intelligence_agent import run_data_intelligence_agent
from agents.synthesis_agent import run_synthesis_agent

_client = None

def _get_client():
    global _client
    if _client is None:
        from agents.base import get_anthropic_client
        _client = get_anthropic_client()
    return _client

ROUTING_SYSTEM_PROMPT = """You are the coordinator for a book intelligence platform. Given a user request, output a JSON routing plan.

Routing rules:
- "how many books", "reading stats", "my library data", "reading history" → data_only
- "find books", "reviews of", "author of", "what is X about" → books_only
- "recommend", "what should I read", "reading brief", "tell me about" → all_agents
- "add to my list", "mark as read", "rate this book" → data_only

Output format: {"agents": ["book_discovery", "data_intelligence", "synthesis"], "book_task": "...", "data_task": "...", "synthesis_task": "..."}
Only include agents that are needed. Always include synthesis if multiple agents are used."""

async def route_request(user_message: str, mcp_tools: Optional[list] = None, read_only: bool = False) -> str:
    if mcp_tools is None:
        mcp_tools = []
    client = _get_client()

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
