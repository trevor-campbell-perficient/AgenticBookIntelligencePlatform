# tests/agents/test_hooks.py
import pytest
from agents.hooks import normalize_timestamps, audit_log_hook

def test_normalize_unix_timestamp():
    tool_result = {"created_at": 1700000000, "title": "Dune"}
    normalized = normalize_timestamps(tool_result)
    assert "T" in normalized["created_at"]  # ISO 8601 format
    assert normalized["title"] == "Dune"

def test_normalize_iso_timestamp_unchanged():
    tool_result = {"created_at": "2024-01-15T10:30:00Z", "title": "Dune"}
    normalized = normalize_timestamps(tool_result)
    assert normalized["created_at"] == "2024-01-15T10:30:00Z"

def test_normalize_handles_non_timestamp_int():
    tool_result = {"page_count": 412, "title": "Dune"}
    normalized = normalize_timestamps(tool_result)
    assert normalized["page_count"] == 412


def test_normalize_nested_dict():
    """Timestamps in nested dicts are also normalized."""
    tool_result = {"book": {"created_at": 1700000000, "title": "Dune"}}
    normalized = normalize_timestamps(tool_result)
    assert "T" in normalized["book"]["created_at"]


def test_normalize_list_of_dicts():
    """Timestamps in list items are also normalized."""
    tool_result = [{"created_at": 1700000000}, {"created_at": 1700000001}]
    normalized = normalize_timestamps(tool_result)
    assert "T" in normalized[0]["created_at"]
    assert "T" in normalized[1]["created_at"]


def test_pre_tool_use_blocks_write_in_read_only_mode():
    from agents.hooks import pre_tool_use_read_only
    result = pre_tool_use_read_only("add_annotation", {"book_id": "b1"}, read_only=True)
    assert result is not None
    assert result["blocked"] is True


def test_pre_tool_use_allows_read_in_read_only_mode():
    from agents.hooks import pre_tool_use_read_only
    result = pre_tool_use_read_only("get_annotations", {"book_id": "b1"}, read_only=True)
    assert result is None


def test_pre_tool_use_allows_write_when_not_read_only():
    from agents.hooks import pre_tool_use_read_only
    result = pre_tool_use_read_only("add_annotation", {"book_id": "b1"}, read_only=False)
    assert result is None


def test_audit_log_hook_does_not_raise(capsys):
    audit_log_hook("session-abc-123", "get_book", {"book_id": "b1"}, {"title": "Dune"})
    captured = capsys.readouterr()
    assert "get_book" in captured.out


def test_audit_log_hook_survives_non_serializable_input(capsys):
    audit_log_hook("session-abc-123", "get_book", {"obj": object()}, None)
    # Must not raise — audit hook must be exception-safe


def test_post_tool_use_normalize_delegates_to_normalize_timestamps():
    from agents.hooks import post_tool_use_normalize
    result = post_tool_use_normalize("some_tool", {"created_at": 1700000000})
    assert "T" in result["created_at"]
