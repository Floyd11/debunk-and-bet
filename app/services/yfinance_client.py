import yfinance as yf
from datetime import datetime
from .sec_edgar import extract_ticker

def get_yfinance_context(question: str, category: str) -> str:
    """
    Synchronous — called via ThreadPoolExecutor.
    Fetches recent company news and earnings date from Yahoo Finance.
    Returns formatted string ready for agent context injection.
    """
    try:
        ticker_str = extract_ticker(question)
        if not ticker_str:
            if category == "macro":
                ticker_str = "SPY"  # market proxy for macro questions
            else:
                return ""

        ticker = yf.Ticker(ticker_str)
        lines = [f"[YAHOO FINANCE — {ticker_str}]"]

        # Recent news (last 5 items)
        news = ticker.news or []
        for item in news[:5]:
            title = item.get("title", "").strip()
            publisher = item.get("publisher", "unknown")
            pub_time = item.get("providerPublishTime", 0)
            if title:
                date_str = datetime.fromtimestamp(pub_time).strftime("%Y-%m-%d") if pub_time else "unknown"
                lines.append(f"- [{date_str}] {title} (via {publisher})")

        # Earnings date if available
        try:
            calendar = ticker.calendar
            if calendar is not None and not calendar.empty:
                earnings_date = calendar.columns[0] if hasattr(calendar, "columns") else None
                if earnings_date:
                    lines.append(f"- Next earnings: {earnings_date}")
        except Exception:
            pass

        return "\n".join(lines) if len(lines) > 1 else ""

    except Exception as e:
        print(f"[YFINANCE ERROR] {e}")
        return ""
