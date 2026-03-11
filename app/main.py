import sys
sys.path.append('/root/edge_protocol')

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
import asyncio
from typing import Dict, Any

from .models import AnalyzeRequest, AnalyzeResponse
from .services.polymarket import get_market_data

from .services.search import get_news_context
from .services.opengradient_client import rewrite_query_with_llm
from .services.polymarket_context import get_polymarket_market_context

import hashlib
import json
import redis
from datetime import date

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# --- Edge Protocol Modules ---
from research.binary_agent import get_binary_research
from research.judge import call_llm_judge
from math_engine.binary_prior import compute_binary_prior
from math_engine.binary_lr import compute_final_lr
from math_engine.binary_bayes import binary_bayesian_update
from edge.binary_filter import evaluate_binary_edge

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
    Main endpoint for analyzing a Polymarket prediction using Edge Protocol modules via OpenGradient TEE.
    """
    try:
        # Cache check
        cache_key = f"analysis:{hashlib.md5(req.url.encode()).hexdigest()}:{date.today()}"
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return AnalyzeResponse(**json.loads(cached))
        except Exception:
            pass  # Redis is unavailable, continue without cache

        # Step 1: Fetch Polymarket Data
        try:
             question, rules, odds = await get_market_data(req.url)
        except Exception as e:
             raise HTTPException(status_code=400, detail=str(e))
             
        # Step 1.1: Fetch Context from Search (DuckDuckGo) using query rewriting
        queries = rewrite_query_with_llm(question)
        
        question_lower = question.lower()
        if "microstrategy" in question_lower or "mstr" in question_lower or "strategy" in question_lower:
            include_domains = ["strategy.com", "sec.gov", "coindesk.com", "bloomberg.com", "prnewswire.com"]
        elif "bitcoin" in question_lower or "crypto" in question_lower:
            include_domains = ["coindesk.com", "cointelegraph.com", "bloomberg.com", "reuters.com"]
        else:
            include_domains = ["reuters.com", "bloomberg.com", "apnews.com", "bbc.com"]
            
        context, sources = await get_news_context(queries, include_domains=include_domains)
        
        # Enrich context with live Polymarket data
        slug = req.url.rstrip('/').split('/')[-1]
        polymarket_live = await get_polymarket_market_context(slug)
        context = context + polymarket_live
        # Step 2: Run Research Agents concurrently via TEE
        try:
            yes_res, no_res = await asyncio.gather(
                get_binary_research(event_title=question, rules=rules, market_id="api", side="YES", context=context),
                get_binary_research(event_title=question, rules=rules, market_id="api", side="NO", context=context),
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM Agent Error: {str(e)}")
        
        # Step 2.5: определяем market_prob до Step 3
        market_prob_yes_float = odds.get('Yes', list(odds.values())[0] if odds else 0.5)

        # Step 3: Compute Binary Prior (теперь с market_prob)
        prior_prob, prior_conf = compute_binary_prior(yes_res, no_res, market_prob_yes_float)
        
        # Step 4: Call Judge for LRs via TEE
        try:
            judge_res, wallet_address = await call_llm_judge(
                question, rules, yes_res, no_res, market_prob_yes_float
            )
            lr_yes = float(judge_res.get("lr_yes", 1.0))
            lr_no = float(judge_res.get("lr_no", 1.0))
            synthesis = str(judge_res.get("synthesis", "Error synthesizing."))
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"LLM Judge Error: {str(e)}")
             
        # Format OpenGradient Explorer link
        explorer_link = f"https://sepolia.basescan.org/address/{wallet_address}#tokentxns" if wallet_address and wallet_address != "0xERROR" else "#"
        
        # Step 5: Synthesize Final LR
        final_lr, lr_conf_mult = compute_final_lr(lr_yes, lr_no)
        
        # Step 6: Bayesian Update
        posterior_prob = binary_bayesian_update(prior_prob, final_lr)
        
        # Step 7: Evaluate Edge & Kelly Sizing
        # market_prob_yes_float is defined earlier at Step 2.5
        
        decision = await evaluate_binary_edge(
            model_prob=posterior_prob,
            market_price=market_prob_yes_float,
            token_id="api",
            days_to_close=10, # default mock
            bankroll=1000.0,  # mock
            confidence_multiplier=lr_conf_mult,
            prior_confidence=prior_conf
        )
        
        # Map decision to frontend expected enums
        if decision.edge > 0:
            recommended_bet = "YES"
        elif decision.edge < 0:
            recommended_bet = "NO"
        else:
            recommended_bet = "SKIP"

        # Format integer probabilities for the UI (0-100)
        ai_prob_int = int(posterior_prob * 100)
        market_prob_int = int(market_prob_yes_float * 100)
        edge_int = int(abs(decision.edge) * 100)
        
        base_rate_text = f"The historical baseline probability is {int(prior_prob*100)}% (Confidence: {prior_conf}). "
        if decision.should_bet:
            base_rate_text += f"Based on the calculated edge, the Kelly criterion recommends allocating {decision.bet_fraction*100:.1f}% of your bankroll to this bet."
        else:
            reason_str = decision.reason.replace('_', ' ')
            base_rate_text += f"However, due to {reason_str}, the Kelly criterion does not recommend allocating more than a minimal fraction (0.0%) of your bankroll to this bet."

        # Step 8: Return formatted JSON
        response = AnalyzeResponse(
            market_question=question,
            recommended_bet=recommended_bet,
            ai_event_probability=ai_prob_int,
            market_probability=market_prob_int,
            edge=edge_int,
            base_rate_analysis=base_rate_text,
            pro_yes_arguments=yes_res.evidence,
            pro_no_arguments=no_res.evidence,
            information_gap=f"Decision Reason: {decision.reason}. Confidence penalty: {lr_conf_mult:.2f}",
            synthesis=synthesis,
            context_sources=list(sources) + [yes_res.base_rate_source, no_res.base_rate_source],
            verification_proof=explorer_link # OpenGradient Trace
        )
        
        # Save to cache
        try:
            redis_client.setex(cache_key, 1800, json.dumps(response.model_dump()))
        except Exception:
            pass  # Redis is unavailable, continue without cache
            
        return response

    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
