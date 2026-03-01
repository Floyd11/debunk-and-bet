from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from .models import AnalyzeRequest, AnalyzeResponse
from .services.polymarket import get_market_data
from .services.search import get_news_context
from .services.opengradient_client import analyze_with_llm

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
             raise HTTPException(status_code=400, detail=f"Polymarket Error: {str(e)}")
        
        # Step 2: Fetch Context from Search (DuckDuckGo)
        context, sources = get_news_context(question)
        
        # Step 3: Analyze with OpenGradient LLM
        try:
             verdict, reasoning, proof_hash = analyze_with_llm(question, rules, odds, context)
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"OpenGradient LLM Error: {str(e)}")
             
        # Format OpenGradient Explorer link based on hash
        explorer_link = f"https://explorer.opengradient.network/tx/{proof_hash}" if proof_hash and proof_hash != "0xERROR" else "#"

        # Step 4: Return formatted JSON
        return AnalyzeResponse(
            market_question=question,
            current_odds=odds,
            ai_verdict=verdict,
            reasoning=reasoning,
            sources=sources,
            verification_proof=explorer_link
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
