import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from importlib import reload

# Ensure coordinator can be imported without real API key
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")


@pytest.mark.asyncio
async def test_coordinator_routes_stats_query_to_data_agent_only():
    """A 'how many books did I read?' query should only invoke the Data Intelligence agent."""
    import agents.coordinator as m
    reload(m)

    with patch.object(m, "run_data_intelligence_agent", new_callable=AsyncMock) as mock_data, \
         patch.object(m, "run_book_discovery_agent", new_callable=AsyncMock) as mock_books, \
         patch.object(m, "run_synthesis_agent", new_callable=AsyncMock) as mock_synth, \
         patch.object(m, "_get_client") as mock_client:
        mock_routing_response = MagicMock()
        mock_routing_response.content = [MagicMock(text='{"agents": ["data_intelligence", "synthesis"], "data_task": "How many books did I read this year?", "synthesis_task": "Summarize the reading stats"}')]
        mock_client.return_value.messages.create.return_value = mock_routing_response
        mock_data.return_value = {"stats": {"read": 42}}
        mock_synth.return_value = "You've read 42 books!"

        result = await m.route_request("How many books did I read this year?")

    mock_data.assert_called_once()
    mock_books.assert_not_called()


@pytest.mark.asyncio
async def test_coordinator_routes_recommendation_to_multiple_agents():
    """A 'what should I read next?' query should invoke both book discovery and data intelligence."""
    import agents.coordinator as m
    reload(m)

    with patch.object(m, "run_data_intelligence_agent", new_callable=AsyncMock) as mock_data, \
         patch.object(m, "run_book_discovery_agent", new_callable=AsyncMock) as mock_books, \
         patch.object(m, "run_synthesis_agent", new_callable=AsyncMock) as mock_synth, \
         patch.object(m, "_get_client") as mock_client:
        mock_routing_response = MagicMock()
        mock_routing_response.content = [MagicMock(text='{"agents": ["book_discovery", "data_intelligence", "synthesis"], "book_task": "Find recommendations", "data_task": "Get reading history", "synthesis_task": "Recommend next book"}')]
        mock_client.return_value.messages.create.return_value = mock_routing_response
        mock_data.return_value = {"reading_history": []}
        mock_books.return_value = {"recommendations": []}
        mock_synth.return_value = "Here are my recommendations..."

        result = await m.route_request("What should I read next?")

    mock_data.assert_called_once()
    mock_books.assert_called_once()
    mock_synth.assert_called_once()
