import os
from typing import Any

import databricks.sql as _databricks_sql
from dotenv import load_dotenv

load_dotenv()

DDL = [
    "CREATE CATALOG IF NOT EXISTS abip",
    "CREATE SCHEMA IF NOT EXISTS abip.books",
    "CREATE SCHEMA IF NOT EXISTS abip.reading",
    "CREATE SCHEMA IF NOT EXISTS abip.intelligence",

    """CREATE TABLE IF NOT EXISTS abip.books.books (
        book_id STRING NOT NULL,
        title STRING,
        authors ARRAY<STRING>,
        isbn STRING,
        isbn13 STRING,
        description STRING,
        genres ARRAY<STRING>,
        page_count INT,
        published_date STRING,
        cover_url STRING,
        average_rating DOUBLE,
        ratings_count INT,
        source STRING,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.books.authors (
        author_id STRING NOT NULL,
        name STRING,
        bio STRING,
        similar_authors ARRAY<STRING>,
        source STRING,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.books.reviews (
        review_id STRING NOT NULL,
        book_id STRING,
        reviewer STRING,
        rating INT,
        review_text STRING,
        review_date STRING,
        source STRING,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.books.enrichment_queue (
        book_id STRING NOT NULL,
        status STRING DEFAULT 'pending',
        queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.books.editions (
        edition_id STRING NOT NULL,
        book_id STRING,
        format STRING,
        language STRING,
        publisher STRING,
        published_date STRING,
        page_count INT,
        source STRING,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.reading.reading_log (
        entry_id STRING NOT NULL,
        book_id STRING,
        title STRING,
        status STRING,
        rating INT,
        started_date STRING,
        finished_date STRING,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.reading.reading_sessions (
        session_id STRING NOT NULL,
        book_id STRING,
        session_date STRING,
        pages_read INT,
        notes STRING,
        mood STRING,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.reading.annotations (
        annotation_id STRING NOT NULL,
        book_id STRING,
        book_title STRING,
        annotation_type STRING,
        content STRING,
        page_number INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.intelligence.reading_briefs (
        book_id STRING NOT NULL,
        brief_text STRING,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.intelligence.book_embeddings (
        book_id STRING NOT NULL,
        embedding ARRAY<DOUBLE>,
        model_version STRING,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",

    """CREATE TABLE IF NOT EXISTS abip.intelligence.audit_log (
        log_id STRING NOT NULL,
        session_id STRING,
        tool_name STRING,
        tool_input STRING,
        tool_result STRING,
        called_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) USING DELTA""",
]


def get_connection() -> Any:
    required = ["DATABRICKS_HOST", "DATABRICKS_HTTP_PATH", "DATABRICKS_TOKEN"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in values."
        )
    return _databricks_sql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"].replace("https://", ""),
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        access_token=os.environ["DATABRICKS_TOKEN"],
    )


def create_schema(cursor: Any) -> None:
    for stmt in DDL:
        try:
            cursor.execute(stmt)
        except Exception as e:
            # Extract first line of statement for readable error message
            first_line = stmt.strip().splitlines()[0]
            raise RuntimeError(f"DDL failed: {first_line!r}") from e


if __name__ == "__main__":
    conn = get_connection()
    with conn.cursor() as cursor:
        create_schema(cursor)
    print("Schema setup complete.")
