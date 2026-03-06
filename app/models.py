from pydantic import BaseModel
from typing import List, Dict, Literal

class AnalyzeRequest(BaseModel):
    url: str

class AnalyzeResponse(BaseModel):
    market_question: str
    recommended_bet: Literal["YES", "NO", "SKIP"]
    ai_event_probability: int
    market_probability: int
    edge: int
    base_rate_analysis: str
    pro_yes_arguments: List[str]
    pro_no_arguments: List[str]
    information_gap: str
    synthesis: str
    context_sources: List[str]
    verification_proof: str
