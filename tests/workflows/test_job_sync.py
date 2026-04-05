import pytest
from unittest.mock import MagicMock, patch, AsyncMock


@pytest.mark.asyncio
async def test_sync_job_upserts_books():
    mock_books = [{"id": "1", "title": "Dune", "author": "Frank Herbert"}]
    with patch("workflows.job_sync.fetch_new_books", new_callable=AsyncMock, return_value=mock_books) as mock_fetch, \
         patch("workflows.job_sync.upsert_books") as mock_upsert:
        from workflows.job_sync import run_sync
        await run_sync()
    mock_upsert.assert_called_once_with(mock_books)


@pytest.mark.asyncio
async def test_sync_job_handles_empty_results():
    with patch("workflows.job_sync.fetch_new_books", new_callable=AsyncMock, return_value=[]) as mock_fetch, \
         patch("workflows.job_sync.upsert_books") as mock_upsert, \
         patch("workflows.job_sync.queue_for_enrichment") as mock_queue:
        from importlib import reload
        import workflows.job_sync as m
        reload(m)
        await m.run_sync()
    mock_upsert.assert_called_once_with([])
    mock_queue.assert_called_once_with([])
