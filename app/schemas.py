from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QuotePoint(BaseModel):
    symbol: str
    price: float
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    market_status: Optional[str] = None
    timestamp: Optional[datetime] = None


class QuoteResponse(BaseModel):
    symbol: str
    price: float
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    market_status: Optional[str] = None
    timestamp: Optional[datetime] = None
    source: str
    research_note: str = "This is research-only market data and not a trading recommendation."


class HistoricalBar(BaseModel):
    timestamp: Optional[datetime] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None


class HistoricalResponse(BaseModel):
    symbol: str
    interval: str
    period: str
    source: str
    data: List[HistoricalBar] = Field(default_factory=list)
    research_note: str = "This is historical research data and not a trading recommendation."


class SignalSummary(BaseModel):
    signal: str
    last_price: float
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    daily_change_pct: Optional[float] = None
    volatility_pct: Optional[float] = None
    price_slope: Optional[float] = None


class SignalResponse(BaseModel):
    symbol: str
    summary: SignalSummary
    research_note: str = "This is a research-only signal summary and not a trade recommendation."


class WatchlistResponse(BaseModel):
    symbols: List[str]
    data: List[QuoteResponse]
