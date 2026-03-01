from typing import List, Tuple
from duckduckgo_search import DDGS
import logging

def get_news_context(query: str) -> Tuple[str, List[str]]:
    """
    Fetches context from DuckDuckGo News Search.
    Returns a combined context string and a list of source URLs.
    """
    context_parts = []
    sources = []
    
    try:
        # Initializing DDGS
        with DDGS() as ddgs:
            # We use text search instead of news as it's often more reliable 
            # and returns richer snippets for prediction markets.
            results = list(ddgs.text(query, max_results=5))
            
            if results:
                context_parts.append("--- DuckDuckGo Search Results ---")
                for item in results:
                    title = item.get("title", "")
                    snippet = item.get("body", "")
                    link = item.get("href", "")
                    
                    context_parts.append(f"Title: {title}\nSnippet: {snippet}")
                    sources.append(link)
            else:
                 context_parts.append("[No relevant search results found]")
                 
    except Exception as e:
        logging.error(f"Error fetching DuckDuckGo results: {e}")
        context_parts.append(f"[Failed to fetch DuckDuckGo results: {str(e)}]")
             
    combined_context = "\n\n".join(context_parts)
    
    if not combined_context.strip():
         combined_context = "No live context available due to search errors."
         
    return combined_context, sources
