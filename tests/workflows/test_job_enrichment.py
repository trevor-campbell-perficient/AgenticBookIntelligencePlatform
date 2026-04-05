import pytest
from unittest.mock import MagicMock, patch, AsyncMock

import workflows.job_enrichment as m


@pytest.mark.asyncio
async def test_generate_reading_brief_returns_string():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="A compelling read about...")]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("workflows.job_enrichment._get_client", return_value=mock_client):
        result = await m.generate_reading_brief({"title": "Dune", "description": "Epic sci-fi"})
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_run_enrichment_processes_pending_books():
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchall.return_value = [("book-1",), ("book-2",)]

    with patch("workflows.job_enrichment.get_cursor", return_value=mock_cursor), \
         patch("workflows.job_enrichment.generate_reading_brief", new_callable=AsyncMock, return_value="Great book!"):
        await m.run_enrichment()
    assert mock_cursor.execute.call_count >= 3  # SELECT + 2 MERGE/UPDATE pairs
