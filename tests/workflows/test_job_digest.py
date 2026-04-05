import pytest
from unittest.mock import MagicMock, patch

import workflows.job_digest as m


@pytest.mark.asyncio
async def test_run_digest_returns_string():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Great week of reading!")]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    mock_stats = {"read": 3, "reading": 1}
    mock_log = [{"title": "Dune"}, {"title": "Foundation"}]

    with patch("workflows.job_digest._get_client", return_value=mock_client), \
         patch("workflows.job_digest.query_reading_log", return_value=mock_log), \
         patch("workflows.job_digest.get_reading_stats", return_value=mock_stats), \
         patch("workflows.job_digest.get_cursor"):
        result = await m.run_digest()
    assert result == "Great week of reading!"
