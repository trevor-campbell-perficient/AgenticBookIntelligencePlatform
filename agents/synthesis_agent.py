import json
from typing import Any

_client = None

def _get_client():
    global _client
    if _client is None:
        from agents.base import get_anthropic_client
        _client = get_anthropic_client()
    return _client

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

SCOPED_TOOLS = {
    "add_annotation", "get_annotations", "search_annotations",
    "add_journal_entry", "get_journal_entries"
}

async def run_synthesis_agent(task: str, context: dict, mcp_tools: list) -> str:
    client = _get_client()
    context_str = json.dumps(context, indent=2)
    user_message = f"Task: {task}\n\nContext from other agents:\n{context_str}"
    messages = [{"role": "user", "content": user_message}]
    annotation_tools = [t for t in mcp_tools if t["name"] in SCOPED_TOOLS]

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
