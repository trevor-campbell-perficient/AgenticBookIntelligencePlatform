from typing import Any
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-4-6")
MAX_TOKENS = 4096


def get_anthropic_client() -> Any:
    """Return an Anthropic client, validating API key is set."""
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable not set.")

    # Parse ANTHROPIC_CUSTOM_HEADERS (newline- or comma-separated "Key: Value" pairs)
    custom_headers: dict[str, str] = {}
    raw_headers = os.environ.get("ANTHROPIC_CUSTOM_HEADERS", "")
    for line in raw_headers.replace(",", "\n").splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            custom_headers[k.strip()] = v.strip()

    kwargs: dict[str, Any] = {"api_key": api_key}
    if custom_headers:
        kwargs["default_headers"] = custom_headers
    if os.environ.get("ANTHROPIC_BASE_URL"):
        kwargs["base_url"] = os.environ["ANTHROPIC_BASE_URL"]

    return anthropic.Anthropic(**kwargs)
