import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import asyncio
from datetime import date

# Import application components
from app.main import AnalyzeRequest, AnalyzeResponse, redis_client, analyze_market
from app.services.polymarket_context import get_polymarket_market_context
from app.services.search import get_news_context

@pytest.mark.asyncio
async def test_redis_cache_hit():
    """Test that a cache hit returns a parsed AnalyzeResponse and skips processing."""
    req = AnalyzeRequest(url="https://polymarket.com/event/example-market")
    
    mock_response_data = {
        "market_question": "Will something happen?",
        "recommended_bet": "YES",
        "ai_event_probability": 75,
        "market_probability": 50,
        "edge": 25,
        "base_rate_analysis": "Test string",
        "pro_yes_arguments": ["Yes"],
        "pro_no_arguments": ["No"],
        "information_gap": "Test info",
        "synthesis": "Test synthesis",
        "context_sources": ["Source 1"],
        "verification_proof": "Proof"
    } # Matches the AnalyzeResponse schema
    
    with patch.object(redis_client, 'get', return_value=json.dumps(mock_response_data)) as mock_get:
        # Invoke the handler directly
        res = await analyze_market(req)
        
        assert isinstance(res, AnalyzeResponse)
        assert res.market_question == "Will something happen?"
        # Ensure the mock was actually called
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_polymarket_context_success():
    """Test the Gamma API context fetch logic and string formatting."""
    mock_data = {
        "volume": "1000",
        "liquidity": "500",
        "bestAsk": "0.55",
        "bestBid": "0.45",
        "endDate": "2024-12-31T23:59:59Z"
    }

    class MockResponse:
        status_code = 200
        def json(self):
            return [mock_data]
            
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MockResponse()
        
        result = await get_polymarket_market_context("test-slug")
        
        assert "Volume: $1000" in result
        assert "Liquidity: $500" in result
        assert "0.45 / 0.55" in result
        assert "2024-12-31" in result

@pytest.mark.asyncio
async def test_search_parallel_execution():
    """Test parallel search executes queries for multiple tiers."""
    queries = ["query 1"]
    
    with patch("app.services.search.TavilyClient.search") as mock_search:
        # Mock what tavily client SDK returns
        mock_search.return_value = {"results": [{"url": "http://test.com", "content": "Test analysis content"}]}
        
        context, sources = await get_news_context(queries)
        
        assert "http://test.com" in sources
        assert "Test analysis content" in context
        
        # Should be called three times for ['d', 'w', 'm']
        assert mock_search.call_count == 3
