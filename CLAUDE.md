# Agentic Book Intelligence Platform

## Project Overview
Multi-agent book intelligence system using Claude SDK, 3 MCP servers, Databricks backend, and Streamlit app.
See `docs/plans/2026-04-04-abip-design.md` for full architecture.

## Tech Stack
- Python 3.11+
- Anthropic SDK for Claude claude-sonnet-4-6 coordinator + subagents
- MCP Python SDK for 3 MCP servers
- Databricks SDK + SQL Connector for Delta Lake
- Streamlit deployed on Databricks Apps

## Coding Standards
- All async where possible (httpx, asyncio)
- Type hints on all function signatures
- Structured error responses from all MCP tools: `{"error": true, "errorCategory": "...", "isRetryable": bool, "message": "..."}`
- No secrets in code — use environment variables
- pytest for all tests; run with `pytest tests/ -v`

## MCP Server Pattern
Each MCP server lives in `mcp_servers/<name>/server.py`. Run with:
`python mcp_servers/<name>/server.py`

## Agent Pattern
Coordinator in `agents/coordinator.py`. Subagents in `agents/<name>_agent.py`.
All agents use `anthropic` sdk with `claude-sonnet-4-6`.

## Environment Variables
See `.env.example` for all required vars. Copy to `.env` and fill in values.
