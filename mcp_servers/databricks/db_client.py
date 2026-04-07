import os
import uuid
from typing import Any, Optional
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

# Lazy import to allow testing without databricks-sql-connector installed
try:
    import databricks.sql as _databricks_sql
    _DATABRICKS_AVAILABLE = True
except ImportError:
    _databricks_sql = None
    _DATABRICKS_AVAILABLE = False


def get_connection() -> Any:
    required = ["DATABRICKS_HOST", "DATABRICKS_HTTP_PATH", "DATABRICKS_TOKEN"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in values."
        )
    if not _DATABRICKS_AVAILABLE:
        raise ImportError(
            "databricks-sql-connector is not installed. Run: pip install databricks-sql-connector"
        )
    return _databricks_sql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"].replace("https://", ""),
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        access_token=os.environ["DATABRICKS_TOKEN"],
    )


@contextmanager
def get_cursor() -> Any:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            yield cursor
    finally:
        conn.close()


def _rows_to_dicts(cursor: Any) -> list[dict[str, Any]]:
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def get_reading_stats() -> dict[str, Any]:
    with get_cursor() as cursor:
        cursor.execute(
            "SELECT status, COUNT(*) as count FROM abip.reading.reading_log GROUP BY status"
        )
        rows = _rows_to_dicts(cursor)
    return {r["status"]: r["count"] for r in rows}


def query_reading_log(status: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
    with get_cursor() as cursor:
        if status:
            cursor.execute(
                "SELECT * FROM abip.reading.reading_log WHERE status = ? ORDER BY updated_at DESC LIMIT ?",
                (status, limit),
            )
        else:
            cursor.execute(
                "SELECT * FROM abip.reading.reading_log ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            )
        return _rows_to_dicts(cursor)


def add_book_to_library(book_id: str, title: str, status: str) -> dict[str, Any]:
    entry_id = str(uuid.uuid4())
    with get_cursor() as cursor:
        cursor.execute(
            """MERGE INTO abip.reading.reading_log AS target
               USING (SELECT ? AS entry_id, ? AS book_id, ? AS title, ? AS status) AS source
               ON target.book_id = source.book_id
               WHEN MATCHED THEN
                 UPDATE SET target.status = source.status, target.updated_at = CURRENT_TIMESTAMP
               WHEN NOT MATCHED THEN
                 INSERT (entry_id, book_id, title, status)
                 VALUES (source.entry_id, source.book_id, source.title, source.status)""",
            (entry_id, book_id, title, status),
        )
    return {"entry_id": entry_id, "book_id": book_id, "title": title, "status": status}


def update_reading_status(book_id: str, status: str, rating: Optional[int] = None) -> dict[str, Any]:
    with get_cursor() as cursor:
        if rating is not None:
            cursor.execute(
                "UPDATE abip.reading.reading_log SET status = ?, rating = ?, updated_at = CURRENT_TIMESTAMP WHERE book_id = ?",
                (status, rating, book_id),
            )
        else:
            cursor.execute(
                "UPDATE abip.reading.reading_log SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE book_id = ?",
                (status, book_id),
            )
    return {"book_id": book_id, "status": status, "rating": rating}
