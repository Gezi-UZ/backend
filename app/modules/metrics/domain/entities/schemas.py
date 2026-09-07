from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class GlobalMetricsResponse(BaseModel):
    total_meters: int
    online_meters: int
    today_revenue: float
    failed_commands: int
    avg_latency_ms: float

class RevenueHistoryItem(BaseModel):
    date: str
    revenue: float
    transactions: int

class MetricsHistoryResponse(BaseModel):
    period: str
    history: List[RevenueHistoryItem]
