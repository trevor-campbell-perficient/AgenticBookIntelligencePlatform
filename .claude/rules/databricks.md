---
paths: ["mcp_servers/databricks/**/*", "workflows/**/*"]
---
# Databricks Rules

- Use `databricks-sdk` for job management and cluster operations
- Use `databricks-sql-connector` for SQL queries against Delta tables
- Always use parameterized queries — never f-string SQL
- Catalog: `abip`, schemas: `books`, `reading`, `intelligence`
- Delta table writes: use `MERGE INTO` for upserts, not `INSERT OVERWRITE`
- Test SQL queries against the warehouse before embedding in code
