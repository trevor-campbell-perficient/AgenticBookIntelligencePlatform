import sqlite3
import uuid
from typing import Any, Optional


class AnnotationsDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS annotations (
                    id TEXT PRIMARY KEY,
                    book_id TEXT NOT NULL,
                    book_title TEXT,
                    annotation_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    page_number INTEGER,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id TEXT PRIMARY KEY,
                    book_id TEXT NOT NULL,
                    book_title TEXT,
                    session_date TEXT NOT NULL,
                    content TEXT NOT NULL,
                    mood TEXT,
                    pages_read INTEGER,
                    created_at TEXT DEFAULT (datetime('now'))
                );
            """)

    def add_annotation(
        self,
        book_id: str,
        book_title: str,
        annotation_type: str,
        content: str,
        page_number: Optional[int] = None,
    ) -> str:
        annotation_id = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO annotations (id, book_id, book_title, annotation_type, content, page_number) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (annotation_id, book_id, book_title, annotation_type, content, page_number),
            )
        return annotation_id

    def get_annotations(self, book_id: Optional[str] = None) -> list[dict[str, Any]]:
        with self._conn() as conn:
            if book_id:
                rows = conn.execute(
                    "SELECT * FROM annotations WHERE book_id = ? ORDER BY created_at DESC",
                    (book_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM annotations ORDER BY created_at DESC"
                ).fetchall()
            return [dict(row) for row in rows]

    def search_annotations(self, query: str) -> list[dict[str, Any]]:
        pattern = f"%{query}%"
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM annotations WHERE content LIKE ? OR book_title LIKE ? ORDER BY created_at DESC",
                (pattern, pattern),
            ).fetchall()
            return [dict(row) for row in rows]

    def add_journal_entry(
        self,
        book_id: str,
        book_title: str,
        session_date: str,
        content: str,
        mood: Optional[str] = None,
        pages_read: Optional[int] = None,
    ) -> str:
        entry_id = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO journal_entries (id, book_id, book_title, session_date, content, mood, pages_read) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (entry_id, book_id, book_title, session_date, content, mood, pages_read),
            )
        return entry_id

    def get_journal_entries(self, book_id: Optional[str] = None) -> list[dict[str, Any]]:
        with self._conn() as conn:
            if book_id:
                rows = conn.execute(
                    "SELECT * FROM journal_entries WHERE book_id = ? ORDER BY session_date DESC",
                    (book_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM journal_entries ORDER BY session_date DESC"
                ).fetchall()
            return [dict(row) for row in rows]
