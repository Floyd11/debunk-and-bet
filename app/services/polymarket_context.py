import httpx

async def get_polymarket_market_context(slug: str) -> str:
    """Fetch live market activity data from Polymarket Gamma API."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"https://gamma-api.polymarket.com/markets",
                params={"slug": slug}
            )
            if response.status_code != 200:
                return ""
                
            data = response.json()
            if not data:
                return ""
                
            market = data[0] if isinstance(data, list) else data
            
            volume = market.get("volume", "N/A")
            liquidity = market.get("liquidity", "N/A")
            best_ask = market.get("bestAsk", "N/A")
            best_bid = market.get("bestBid", "N/A")
            close_time = market.get("endDate", "N/A")
            
            return (
                f"\n\n### POLYMARKET LIVE DATA:\n"
                f"- 24h Volume: ${volume}\n"
                f"- Liquidity: ${liquidity}\n"
                f"- Best Bid/Ask: {best_bid} / {best_ask}\n"
                f"- Market closes: {close_time}\n"
            )
    except Exception as e:
        print(f"Polymarket context error: {e}")
        return ""
