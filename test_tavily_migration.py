import os
from dotenv import load_dotenv
from app.services.search import get_news_context

load_dotenv()

def test_tavily_search():
    print("Testing Tavily Search Integration...\n")
    queries = ["Iran Israel conflict latest"]
    
    context, sources = get_news_context(queries)
    
    print(context)
    print("\n\n--- Extracted Context Sources ---")
    for s in sources:
        print(s)
        
    assert "https://" in context, "Context output should contain URLs"
    assert len(sources) > 0, "Should have extracted at least one URL"
    assert "### TIMELINE OF EVENTS:" in context, "Should have timeline header"

if __name__ == "__main__":
    test_tavily_search()
