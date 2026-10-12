from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    message: str
    file_name: str
    rows: int
    summary: Dict[str, Any]


class ChatTurn(BaseModel):
    role: str
    content: str


class ChartContext(BaseModel):
    title: str = 'Chart'
    data: List[Dict[str, Any]] = Field(default_factory=list)


class AIQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    context_filters: Optional[Dict[str, Any]] = None
    conversation_history: Optional[List[ChatTurn]] = None
    chart_context: Optional[ChartContext] = None
    stream: bool = True


class ScenarioRequest(BaseModel):
    delay_days: float = 0
    lead_time_spike_pct: float = 0
    demand_shift_pct: float = 0
    safety_stock_multiplier: float = 1.0
    price_change_pct: float = 0
    price_elasticity_factor: Optional[float] = None
    context_filters: Optional[Dict[str, Any]] = None
    include_narrative: bool = True


class DatasetLoadRequest(BaseModel):
    file_name: str
