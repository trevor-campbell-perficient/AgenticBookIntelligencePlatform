import json
import re
from datetime import datetime, timezone
from typing import Any, Optional

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


def pre_tool_use_read_only(tool_name: str, tool_input: dict, read_only: bool = False) -> Optional[dict]:
    """PreToolUse hook: block write operations in read-only mode.
    Returns None to allow, or an error dict to block.
    """
    WRITE_TOOLS = {
        "add_book_to_library",
        "update_reading_status",
        "add_annotation",
        "add_journal_entry",
        "trigger_enrichment_job",
    }
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
