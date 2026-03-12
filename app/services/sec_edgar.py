import httpx
import asyncio
import re

TICKER_PATTERNS = {
    "microstrategy": "MSTR",
    "tesla":         "TSLA",
    "apple":         "AAPL",
    "microsoft":     "MSFT",
    "nvidia":        "NVDA",
    "coinbase":      "COIN",
    "meta":          "META",
    "amazon":        "AMZN",
    "google":        "GOOGL",
    "alphabet":      "GOOGL",
}

def extract_ticker(question: str) -> str | None:
    q = question.lower()
    for keyword, ticker in TICKER_PATTERNS.items():
        if keyword in q:
            return ticker
    match = re.search(r'\b([A-Z]{2,5})\b', question)
    return match.group(1) if match else None

async def get_sec_context(question: str, max_filings: int = 5) -> str:
    """
    Fetches recent SEC 8-K filings for company mentioned in question.
    8-K = material events (earnings, acquisitions, buybacks).
    Fails silently if SEC API is unavailable or blocks the request.
    Returns formatted string ready for agent context injection.
    """
    try:
        ticker = extract_ticker(question)
        if not ticker:
            return ""

        # FIXED: use search_url variable consistently — single source of truth for the endpoint
        search_url = (
            f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22"
            f"&forms=8-K&dateRange=custom&startdt=2025-01-01"
        )
        headers = {"User-Agent": "EdgeProtocol research@edgeprotocol.com"}

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(search_url, headers=headers)
            if resp.status_code != 200:
                return ""

            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            if not hits:
                return ""

            lines = [f"[SEC EDGAR — {ticker} Recent 8-K Filings]"]
            for hit in hits[:max_filings]:
                source = hit.get("_source", {})
                filed = source.get("file_date", "unknown")
                description = source.get("display_names", [""])[0] if source.get("display_names") else ""
                form = source.get("form_type", "8-K")
                lines.append(f"- [{filed}] {form}: {description}")

            return "\n".join(lines)

    except Exception as e:
        print(f"[SEC EDGAR ERROR] {e}")
        return ""
