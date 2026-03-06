import os
import logging
from typing import List, Tuple
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

def get_news_context(queries: List[str]) -> Tuple[str, set]:
    """
    Fetches context from Tavily using multiple targeted queries.
    Enforces a 3-tier time bucket strategy.
    Returns a combined context string and a set of source URLs.
    """
    context_parts = []
    sources = set()
    
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logging.error("TAVILY_API_KEY is not set.")
        return ("### TIMELINE OF EVENTS:\n[No live context available due to missing API key.]", set())
        
    tavily_client = TavilyClient(api_key=api_key)

    tiers = {
        "d": {"header": "[🔴 URGENT: LAST 24 HOURS]", "days": 1, "max_results": 3, "items": []},
        "w": {"header": "[🟡 RECENT: LAST 7 DAYS]", "days": 7, "max_results": 3, "items": []},
        "m": {"header": "[🔵 BACKGROUND: LAST 30 DAYS]", "days": 30, "max_results": 4, "items": []},
    }

    try:
        found_results = False
        
        for query in queries:
            logging.info(f"Searching Tavily for: {query}")
            
            for tier_key in ["d", "w", "m"]:
                tier_info = tiers[tier_key]
                try:
                    response = tavily_client.search(
                        query=query,
                        days=tier_info["days"],
                        max_results=tier_info["max_results"],
                        search_depth="advanced",
                        include_raw_content=False
                    )
                    
                    if response and "results" in response:
                        for result in response["results"]:
                            url = result.get("url", "")
                            if not url or url in sources:
                                continue
                            
                            content = result.get("content", "")
                            tier_info["items"].append(f"Source: {url} - {content}")
                            sources.add(url)
                            found_results = True

                except Exception as e:
                    print(f"Tavily Error: {e}")
                    logging.error(f"Error in Tavily tier {tier_key} for query '{query}': {e}")
                    
        context_parts.append("### TIMELINE OF EVENTS:")
        
        if found_results:
            for tier_key in ["d", "w", "m"]:
                tier_data = tiers[tier_key]
                if tier_data["items"]:
                    context_parts.append(tier_data["header"])
                    for item_str in tier_data["items"]:
                        context_parts.append(f"- {item_str}")
        else:
            context_parts.append("[No relevant search results found]")
            
    except Exception as e:
        print(f"Tavily Error: {e}")
        logging.error(f"Error fetching Tavily results: {e}")
        context_parts.append("### TIMELINE OF EVENTS:")
        context_parts.append(f"[Failed to fetch search results: {str(e)}]")
              
    combined_context = "\n\n".join(context_parts)
    
    if not combined_context.strip():
         combined_context = "### TIMELINE OF EVENTS:\n[No live context available due to search errors.]"
         
    return combined_context, sources
