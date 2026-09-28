from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.providers.factory import ProviderFactory
from app.schemas import HistoricalResponse, QuoteResponse, SignalResponse, WatchlistResponse

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


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
        "provider": settings.data_provider,
        "research_only": True,
    }


@app.get("/providers")
def providers() -> Dict[str, Any]:
    provider_names = ["yahoo", "alpha_vantage", "finnhub", "polygon"]
    return {
        "configured_provider": settings.data_provider,
        "available_providers": provider_names,
        "research_only": True,
    }


@app.get("/quote/{symbol}", response_model=QuoteResponse)
def get_quote(symbol: str) -> QuoteResponse:
    provider = ProviderFactory.create(settings.data_provider)
    return provider.get_quote(symbol)


@app.get("/historical/{symbol}", response_model=HistoricalResponse)
def get_historical(
    symbol: str,
    period: str = Query(default="1mo", description="Example: 1d, 5d, 1mo, 3mo, 6mo, 1y"),
    interval: str = Query(default="1d", description="Example: 1d, 5d, 1wk, 1mo"),
) -> HistoricalResponse:
    provider = ProviderFactory.create(settings.data_provider)
    return provider.get_historical(symbol, period=period, interval=interval)


@app.get("/signals/{symbol}", response_model=SignalResponse)
def get_signals(symbol: str) -> SignalResponse:
    provider = ProviderFactory.create(settings.data_provider)
    data = provider.get_historical(symbol, period="6mo", interval="1d")

    if not data.data:
        raise HTTPException(status_code=404, detail=f"No historical data found for {symbol}")

    close_prices = [point.close for point in data.data if point.close is not None]
    if len(close_prices) < 3:
        raise HTTPException(status_code=422, detail=f"Not enough price points to compute signals for {symbol}")

    last_price = close_prices[-1]
    sma_20 = sum(close_prices[-20:]) / min(20, len(close_prices))
    sma_50 = sum(close_prices[-50:]) / min(50, len(close_prices))
    latest_delta = ((last_price - close_prices[-2]) / close_prices[-2]) * 100 if close_prices[-2] else 0.0
    volatility = 0.0
    if len(close_prices) > 1:
        returns = [
            ((close_prices[i] - close_prices[i - 1]) / close_prices[i - 1]) * 100
            for i in range(1, len(close_prices))
        ]
        volatility = sum(abs(r) for r in returns) / len(returns) if returns else 0.0

    slope = 0.0
    if len(close_prices) >= 2:
        slope = (close_prices[-1] - close_prices[0]) / max(1, len(close_prices) - 1)

    signal = "neutral"
    if last_price > sma_20 and last_price > sma_50:
        signal = "bullish"
    elif last_price < sma_20 and last_price < sma_50:
        signal = "bearish"

    return SignalResponse(
        symbol=symbol.upper(),
        summary={
            "signal": signal,
            "last_price": last_price,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "daily_change_pct": latest_delta,
            "volatility_pct": volatility,
            "price_slope": slope,
        },
        research_note="This is a research-only signal summary and not a trade recommendation.",
    )


@app.get("/watchlist", response_model=WatchlistResponse)
def get_watchlist(symbols: Optional[List[str]] = Query(default=None)) -> WatchlistResponse:
    if not symbols:
        raise HTTPException(status_code=400, detail="Provide at least one symbol in the symbols query parameter.")

    provider = ProviderFactory.create(settings.data_provider)
    quotes = [provider.get_quote(symbol) for symbol in symbols]

    return WatchlistResponse(
        symbols=[quote.symbol for quote in quotes],
        data=quotes,
    )
