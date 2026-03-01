from pydantic import BaseModel, BaseModel
from typing import List, Dict, Literal

class AnalyzeRequest(BaseModel):
    url: str

class AnalyzeResponse(BaseModel):
    market_question: str
    current_odds: Dict[str, float]
    ai_verdict: Literal["Yes", "No", "Uncertain"]
    reasoning: str
    sources: List[str]
    verification_proof: str
