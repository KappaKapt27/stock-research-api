from __future__ import annotations

from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.cache import CacheStore
from app.config import settings
from app.dashboard import build_dashboard_html
from app.providers.factory import ProviderFactory
from app.schemas import HistoricalResponse, ProviderStatusResponse, QuoteResponse, SignalResponse, WatchlistResponse
from app.services import MarketDataService

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Research-only stock analysis API. No live trading or order execution.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

market_service = MarketDataService()
cache_store = CacheStore()


@app.get("/")
def root() -> HTMLResponse:
    return build_dashboard_html()


@app.get("/dashboard")
def dashboard() -> HTMLResponse:
    return build_dashboard_html()


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
        "provider": settings.data_provider,
        "research_only": True,
    }


@app.get("/providers", response_model=ProviderStatusResponse)
def provider_status() -> ProviderStatusResponse:
    return ProviderStatusResponse.model_validate(market_service.provider_status())


@app.get("/quote/{symbol}", response_model=QuoteResponse)
def get_quote(symbol: str) -> QuoteResponse:
    payload = market_service.get_quote(symbol)
    return QuoteResponse.model_validate(payload)


@app.get("/historical/{symbol}", response_model=HistoricalResponse)
def get_historical(
    symbol: str,
    period: str = Query(default="1mo", description="Example: 1d, 5d, 1mo, 3mo, 6mo, 1y"),
    interval: str = Query(default="1d", description="Example: 1d, 5d, 1wk, 1mo"),
) -> HistoricalResponse:
    payload = market_service.get_historical(symbol, period=period, interval=interval)
    return HistoricalResponse.model_validate(payload)


@app.get("/signals/{symbol}", response_model=SignalResponse)
def get_signals(symbol: str) -> SignalResponse:
    payload = market_service.get_signals(symbol)
    return SignalResponse.model_validate(payload)


@app.get("/watchlist", response_model=WatchlistResponse)
def get_watchlist(symbols: str = Query(default=settings.default_symbols, description="Comma-separated symbols.")) -> WatchlistResponse:
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="Provide at least one symbol in the symbols query parameter.")
    payload = market_service.get_watchlist(symbol_list)
    return WatchlistResponse.model_validate(payload)


@app.post("/cache/clear")
def clear_cache() -> Dict[str, str]:
    cache_store.clear()
    return {"status": "ok", "message": "Cache cleared."}
