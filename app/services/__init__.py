from __future__ import annotations

from app.cache import CacheStore
from app.config import settings
from app.providers.factory import ProviderFactory


class MarketDataService:
    def __init__(self, provider_name: str | None = None, cache_store: CacheStore | None = None):
        self.provider = ProviderFactory.create(provider_name or settings.data_provider)
        self.cache_store = cache_store or CacheStore()

    def _read_or_fetch(self, cache_key: str, fetcher, ttl_seconds: int = 300):
        cached = self.cache_store.get(cache_key)
        if cached is not None:
            return cached
        value = fetcher()
        self.cache_store.set(cache_key, value, ttl_seconds=ttl_seconds)
        return value

    def get_quote(self, symbol: str):
        symbol = symbol.upper().strip()
        return self._read_or_fetch(
            f"quote:{self.provider.name}:{symbol}",
            lambda: self.provider.get_quote(symbol).model_dump(mode="json"),
            ttl_seconds=300,
        )

    def get_historical(self, symbol: str, period: str = "1mo", interval: str = "1d"):
        symbol = symbol.upper().strip()
        return self._read_or_fetch(
            f"historical:{self.provider.name}:{symbol}:{period}:{interval}",
            lambda: self.provider.get_historical(symbol, period=period, interval=interval).model_dump(mode="json"),
            ttl_seconds=600,
        )

    def get_signals(self, symbol: str):
        historical = self.get_historical(symbol=symbol, period="6mo", interval="1d")
        data = historical.get("data", [])
        closes = [float(item.get("close")) for item in data if item.get("close") is not None]
        if len(closes) < 2:
            raise ValueError(f"Not enough data to compute signals for {symbol}.")

        last_price = closes[-1]
        sma_20 = sum(closes[-20:]) / min(20, len(closes))
        sma_50 = sum(closes[-50:]) / min(50, len(closes))
        previous = closes[-2] if len(closes) >= 2 else last_price
        daily_change_pct = ((last_price - previous) / previous * 100) if previous else 0.0

        returns = [
            ((closes[i] - closes[i - 1]) / closes[i - 1]) * 100
            for i in range(1, len(closes))
            if closes[i - 1] not in (None, 0)
        ]
        volatility_pct = sum(abs(r) for r in returns) / len(returns) if returns else 0.0
        price_slope = (closes[-1] - closes[0]) / max(1, len(closes) - 1)

        if last_price > sma_20 and last_price > sma_50:
            signal = "bullish"
        elif last_price < sma_20 and last_price < sma_50:
            signal = "bearish"
        else:
            signal = "neutral"

        return {
            "symbol": symbol.upper(),
            "summary": {
                "signal": signal,
                "last_price": last_price,
                "sma_20": sma_20,
                "sma_50": sma_50,
                "daily_change_pct": daily_change_pct,
                "volatility_pct": volatility_pct,
                "price_slope": price_slope,
            },
            "research_note": "This is a research-only signal summary and not a trade recommendation.",
        }

    def get_watchlist(self, symbols):
        quotes = []
        for symbol in symbols:
            quote_payload = self.get_quote(symbol)
            quotes.append(quote_payload)
        return {"symbols": [str(item["symbol"]) for item in quotes], "data": quotes}

    def provider_status(self):
        statuses = []
        for name in ["yahoo", "alpha_vantage", "finnhub", "polygon"]:
            configured = False
            if name == "yahoo":
                configured = True
            elif name == "alpha_vantage":
                configured = bool(settings.alpha_vantage_api_key)
            elif name == "finnhub":
                configured = bool(settings.finnhub_api_key)
            elif name == "polygon":
                configured = bool(settings.polygon_api_key)

            statuses.append(
                {
                    "name": name,
                    "configured": configured,
                    "supported": True,
                    "note": "Research-only provider status.",
                }
            )
        return {"configured_provider": settings.data_provider, "providers": statuses, "research_only": True}
