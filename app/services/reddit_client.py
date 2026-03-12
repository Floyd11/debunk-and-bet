import praw
import os
from datetime import datetime, timezone

# Category → subreddit mapping
CATEGORY_SUBREDDITS = {
    "crypto":      ["bitcoin", "ethfinance", "CryptoCurrency", "solana"],
    "geopolitics": ["geopolitics", "worldnews", "CredibleDefense"],
    "corporate":   ["investing", "stocks", "wallstreetbets"],
    "macro":       ["economics", "investing", "financialindependence"],
    "other":       ["geopolitics", "worldnews"],
}

def get_reddit_context(query: str, category: str, max_posts: int = 5) -> str:
    """
    Synchronous — called via ThreadPoolExecutor.
    Fetches top posts matching query from category-specific subreddits.
    Returns formatted string ready for agent context injection.
    """
    try:
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT", "EdgeProtocol/1.0"),
        )

        subreddits = CATEGORY_SUBREDDITS.get(category, CATEGORY_SUBREDDITS["other"])
        subreddit_str = "+".join(subreddits)
        subreddit = reddit.subreddit(subreddit_str)

        results = []
        for post in subreddit.search(query, sort="new", time_filter="week", limit=max_posts):
            score = post.score
            title = post.title.strip()
            created = datetime.fromtimestamp(post.created_utc, tz=timezone.utc).strftime("%Y-%m-%d")
            results.append(f"- [{created}] {title} (↑{score})")

        if not results:
            return ""

        lines = [f"[REDDIT SENTIMENT — r/{subreddit_str}]"] + results
        return "\n".join(lines)

    except Exception as e:
        print(f"[REDDIT ERROR] {e}")
        return ""
