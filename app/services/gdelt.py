import httpx
import asyncio
from urllib.parse import quote

async def get_gdelt_context(query: str, max_articles: int = 5) -> str:
    """
    Fetches recent news from GDELT Project API.
    Best for: geopolitics, international events, anything Tavily misses.
    Returns formatted string ready for agent context injection.
    """
    try:
        encoded = quote(query)
        url = (
            f"https://api.gdeltproject.org/api/v2/doc/doc"
            f"?query={encoded}&mode=artlist&maxrecords={max_articles}"
            f"&format=json&sort=DateDesc"
        )
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return ""
            data = response.json()
            articles = data.get("articles", [])
            if not articles:
                return ""

            lines = ["[GDELT NEWS CONTEXT]"]
            for article in articles:
                title = article.get("title", "").strip()
                source = article.get("domain", "unknown")
                date = article.get("seendate", "")[:8]  # YYYYMMDD
                if title:
                    lines.append(f"- [{date}] {title} (via {source})")

            return "\n".join(lines)

    except Exception as e:
        print(f"[GDELT ERROR] {e}")
        return ""
