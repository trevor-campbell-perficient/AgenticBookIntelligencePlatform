---
paths: ["mcp_servers/**/*"]
---
# MCP Server Rules

- All tools must return structured errors: `{"error": true, "errorCategory": "transient|validation|permission|business", "isRetryable": bool, "message": "..."}`
- Tool descriptions must clearly differentiate from similar tools — include input format, example, and when-to-use-vs-alternative
- Never raise unhandled exceptions from tool handlers — catch and return structured error
- Each server runs on stdio transport (default MCP)
- Test each tool handler independently before integration testing
