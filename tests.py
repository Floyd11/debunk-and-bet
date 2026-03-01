import pytest
import asyncio
from app.services.polymarket import get_market_data

@pytest.mark.asyncio
async def test_get_market_data_invalid_url():
    url = "https://invalid-url.com"
    with pytest.raises(ValueError, match="Invalid Polymarket URL"):
        await get_market_data(url)

# A real mock test would mock `httpx.AsyncClient` 
# For demonstration in this boilerplate, we just ensure the regex parsing works.
@pytest.mark.asyncio
async def test_get_market_data_extracts_slug():
    url = "https://polymarket.com/event/will-bitcoin-hit-100k-in-2024"
    # We expect this to fail with httpx.HTTPStatusError or connection error
    # but the slug extraction part runs first.
    try:
        await get_market_data(url)
    except Exception as e:
        # If the URL parsing failed, it would raise ValueError "Invalid Polymarket URL"
        assert "Invalid Polymarket URL" not in str(e)
