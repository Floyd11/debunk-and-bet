from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from .models import AnalyzeRequest, AnalyzeResponse
from .services.polymarket import get_market_data
from .services.search import get_news_context
from .services.opengradient_client import analyze_with_llm, rewrite_query_with_llm

app = FastAPI(title="Debunk & Bet API")

# Serve static files (Frontend JS/CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serves the main frontend page"""
    with open("static/index.html", "r") as f:
        return f.read()

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_market(req: AnalyzeRequest):
    """
    Main endpoint for analyzing a Polymarket prediction.
    """
    try:
        # Step 1: Fetch Polymarket Data
        try:
             question, rules, odds = await get_market_data(req.url)
        except Exception as e:
             # Just pass the error string directly so custom messages show up cleanly
             raise HTTPException(status_code=400, detail=str(e))
        
        # Step 2: Rewrite Query
        queries = rewrite_query_with_llm(question)
             
        # Step 3: Fetch Context from Search (DuckDuckGo) using multiple queries
        context, sources = get_news_context(queries)
        
        # Step 4: Analyze with OpenGradient LLM
        try:
             analysis_result = analyze_with_llm(question, rules, odds, context)
             true_probability_yes = analysis_result.get("true_probability_yes", 50)
             wallet_address = analysis_result.get("wallet_address", "0xERROR")
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"OpenGradient LLM Error: {str(e)}")
             
        # Format OpenGradient Explorer link to point to user's wallet token transactions
        explorer_link = f"https://sepolia.basescan.org/address/{wallet_address}#tokentxns" if wallet_address and wallet_address != "0xERROR" else "#"

        # Step 5: Backend Decision Logic
        # Assuming binary market, YES is usually the first key or 'Yes' key.
        market_prob_yes_float = odds.get('Yes', list(odds.values())[0] if odds else 0.5)
        market_prob_yes = int(market_prob_yes_float * 100)
        
        if true_probability_yes > market_prob_yes:
            recommended_bet = "YES"
        elif true_probability_yes < market_prob_yes:
            recommended_bet = "NO"
        else:
            recommended_bet = "SKIP"
            
        edge = abs(true_probability_yes - market_prob_yes)

        # Step 6: Return formatted JSON
        return AnalyzeResponse(
            market_question=question,
            recommended_bet=recommended_bet,
            ai_event_probability=true_probability_yes,
            market_probability=market_prob_yes,
            edge=edge,
            base_rate_analysis=analysis_result.get("base_rate_analysis", ""),
            pro_yes_arguments=analysis_result.get("pro_yes_arguments", []),
            pro_no_arguments=analysis_result.get("pro_no_arguments", []),
            information_gap=analysis_result.get("information_gap", ""),
            synthesis=analysis_result.get("synthesis", ""),
            context_sources=list(sources), # convert set back to list
            verification_proof=explorer_link
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

