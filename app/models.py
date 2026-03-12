from pydantic import BaseModel
from typing import List, Dict, Literal, Optional

class AnalyzeRequest(BaseModel):
    url: str

class AnalyzeResponse(BaseModel):
    market_id: str
    market_slug: str
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

class CategoryStat(BaseModel):
    resolved_count: int
    accuracy: Optional[float]
    avg_brier_score: Optional[float]

class StatsResponse(BaseModel):
    total_predictions: int
    total_resolved: int
    overall_accuracy: Optional[float]
    overall_brier_score: Optional[float]
    by_category: Dict[str, CategoryStat]
