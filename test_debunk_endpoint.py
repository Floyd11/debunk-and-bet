import sys
import asyncio
sys.path.append('/root/gradient')
sys.path.append('/root/edge_protocol')

from unittest.mock import patch, MagicMock
from app.models import AnalyzeRequest
from app.main import analyze_market

async def run_test():
    mock_pm_data = ("Will Ethereum reach $4000 before the end of March 2026?", "Resolves to Yes if Ethereum price hits 4000 USD on Binance.", {"Yes": 0.40, "No": 0.60})
    
    mock_llm_json_yes = '{"candidate_side": "YES", "base_rate_value": 0.30, "base_rate_n": 10, "base_rate_source": "Historical Bull Runs", "evidence": ["Upward trend since Jan", "ETF inflows"], "confidence": "normal"}'
    mock_llm_json_no = '{"candidate_side": "NO", "base_rate_value": 0.80, "base_rate_n": 15, "base_rate_source": "Macro Resistance Data", "evidence": ["Fed rate hold", "Resistance at 3800"], "confidence": "normal"}'
    
    mock_judge_result = ({"lr_yes": 2.5, "lr_no": 1.2, "synthesis": "YES evidence is much stronger"}, "0xMOCKWALLETID")

    with patch('app.main.get_market_data') as mock_pm, \
         patch('app.main.rewrite_query_with_llm') as mock_rewrite, \
         patch('app.main.get_news_context') as mock_search, \
         patch('research.binary_agent.llm_call') as mock_llm, \
         patch('app.main.call_llm_judge') as mock_judge:
         
        mock_pm.return_value = mock_pm_data
        mock_rewrite.return_value = ["ethereum price prediction"]
        mock_search.return_value = ("Recent news shows ETH surging.", ["source1.com"])
        
        async def side_effect(prompt, **kwargs):
            if 'ДА' in prompt: return mock_llm_json_yes
            return mock_llm_json_no
            
        mock_llm.side_effect = side_effect
        mock_judge.return_value = mock_judge_result
        
        req = AnalyzeRequest(url="https://polymarket.com/event/eth-4k")
        response = await analyze_market(req)
        
        print("--- GENERATED RESPONSE JSON ---")
        print(response.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(run_test())
