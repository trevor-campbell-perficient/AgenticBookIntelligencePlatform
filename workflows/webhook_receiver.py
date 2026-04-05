import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from fastapi import FastAPI, Request as FastAPIRequest
    app = FastAPI()
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    app = None


if _FASTAPI_AVAILABLE:
    @app.post("/webhook/hardcover")
    async def hardcover_webhook(request: FastAPIRequest) -> dict:
        """Receive new book events from Hardcover, queue for enrichment using MERGE INTO."""
        payload = await request.json()
        book_id = payload.get("book_id")
        if not book_id:
            return {"status": "ignored"}
        try:
            from mcp_servers.databricks.db_client import get_cursor
            with get_cursor() as cursor:
                cursor.execute(
                    """MERGE INTO abip.books.enrichment_queue AS target
                       USING (SELECT %s AS book_id) AS source
                       ON target.book_id = source.book_id
                       WHEN NOT MATCHED THEN INSERT (book_id, status)
                           VALUES (source.book_id, 'pending')""",
                    (book_id,),
                )
            return {"status": "queued", "book_id": book_id}
        except Exception as e:
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
