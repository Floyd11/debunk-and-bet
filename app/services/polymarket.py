import httpx
from typing import Dict, Any, Tuple
import re

async def get_market_data(url: str) -> Tuple[str, str, Dict[str, float]]:
    """
    Fetches market data from Polymarket API given a market URL.
    Returns: (question, resolution_rules, current_odds)
    """
    # Extract slug from URL
    match = re.search(r'/event/([^/?#]+)', url)
    if not match:
        raise ValueError("Invalid Polymarket URL: Could not extract event slug.")
    
    slug = match.group(1)
    
    api_url = f"https://gamma-api.polymarket.com/events?slug={slug}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url)
        response.raise_for_status()
        
        data = response.json()
        if not data:
            raise ValueError(f"No event found for slug: {slug}")
        
        event = data[0]
        question = event.get("title", "Unknown Question")
        resolution_rules = event.get("description", "No rules provided.")
        
        # Determine odds from tokens and markets
        # Assuming binary market for simplicity (Yes/No)
        markets = event.get("markets", [])
        if not markets:
            raise ValueError("No markets found for this event.")
            
        main_market = markets[0]
        import json
        
        raw_outcomes = main_market.get("outcomes", "[]")
        raw_prices = main_market.get("outcomePrices", "[]")
        
        try:
             outcomes = json.loads(raw_outcomes) if isinstance(raw_outcomes, str) else raw_outcomes
             prices = json.loads(raw_prices) if isinstance(raw_prices, str) else raw_prices
        except json.JSONDecodeError:
             outcomes, prices = [], []
        
        odds = {}
        for i, outcome in enumerate(outcomes):
            try:
                price = float(prices[i]) if i < len(prices) else 0.0
                odds[outcome] = price
            except (ValueError, TypeError):
                odds[outcome] = 0.0
                
        return question, resolution_rules, odds
