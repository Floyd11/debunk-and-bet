import os
import logging
import asyncio
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

OFFICIAL_DOMAINS = {
    "microstrategy": ["strategy.com", "sec.gov", "coindesk.com", "bloomberg.com"],
    "default": ["reuters.com", "bloomberg.com", "coindesk.com", "ap.org"]
}

_executor = ThreadPoolExecutor(max_workers=6)

def _search_single(tavily_client, query: str, tier_key: str, tier_info: dict, include_domains: List[str] = None) -> list:
    """Single blocking Tavily search — runs in thread pool."""
    try:
        search_params = {
            "query": query,
            "days": tier_info["days"],
            "max_results": tier_info["max_results"],
            "search_depth": "advanced" if tier_key == "d" else "basic",
            "include_raw_content": False
        }
        if tier_key == "d" and include_domains:
            search_params["include_domains"] = include_domains
            
        response = tavily_client.search(**search_params)
        return response.get("results", []) if response else []
    except Exception as e:
        logging.error(f"Tavily Error [{tier_key}] '{query}': {e}")
        return []

async def get_news_context(queries: List[str], include_domains: List[str] = None) -> Tuple[str, set]:
    """Parallel Tavily search across all queries and tiers simultaneously."""
    context_parts = []
    sources = set()
    
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logging.error("TAVILY_API_KEY is not set.")
        return ("### TIMELINE OF EVENTS:\n[No live context available due to missing API key.]", set())
    
    tavily_client = TavilyClient(api_key=api_key)
    
    tiers = {
        "d": {"header": "[🔴 URGENT: LAST 24 HOURS]", "days": 1, "max_results": 4, "items": []},
        "w": {"header": "[🟡 RECENT: LAST 7 DAYS]", "days": 7, "max_results": 4, "items": []},
        "m": {"header": "[🔵 BACKGROUND: LAST 14 DAYS]", "days": 14, "max_results": 2, "items": []},
    }
    
    loop = asyncio.get_running_loop()
    
    tasks = []
    task_meta = []
    for query in queries:
        for tier_key, tier_info in tiers.items():
            tasks.append(
                loop.run_in_executor(_executor, _search_single, tavily_client, query, tier_key, tier_info, include_domains)
            )
            task_meta.append((tier_key, query))
            
    all_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for (tier_key, query), results in zip(task_meta, all_results):
        if isinstance(results, Exception):
            continue
        for result in results:
            url = result.get("url", "")
            if not url or url in sources:
                continue
            content = result.get("content", "")
            tiers[tier_key]["items"].append(f"Source: {url} - {content}")
            sources.add(url)
            
    context_parts.append("### TIMELINE OF EVENTS:")
    found = False
    for tier_key in ["d", "w", "m"]:
        tier_data = tiers[tier_key]
        if tier_data["items"]:
            context_parts.append(tier_data["header"])
            for item_str in tier_data["items"]:
                context_parts.append(f"- {item_str}")
            found = True
            
    if not found:
        context_parts.append("[No relevant search results found]")
        
    return "\n\n".join(context_parts), sources
