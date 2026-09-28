from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.config import settings
from app.schemas import HistoricalResponse, HistoricalBar, QuoteResponse


class StockDataProvider(ABC):
    name: str

    @abstractmethod
    def get_quote(self, symbol: str) -> QuoteResponse:
        raise NotImplementedError

    @abstractmethod
    def get_historical(self, symbol: str, period: str = "1mo", interval: str = "1d") -> HistoricalResponse:
        raise NotImplementedError


class YahooFinanceProvider(StockDataProvider):
    name = "yahoo"

    def get_quote(self, symbol: str) -> QuoteResponse:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        price = float(info.get("last_price") or info.get("lastPrice") or 0.0)
        previous_close = float(info.get("previous_close") or info.get("regularMarketPreviousClose") or 0.0)
        change = price - previous_close if previous_close else 0.0
        change_pct = (change / previous_close * 100) if previous_close else 0.0
        return QuoteResponse(
            symbol=symbol.upper(),
            price=price,
            previous_close=previous_close,
            change=change,
            change_pct=change_pct,
            market_status="open",
            source=self.name,
        )

    def get_historical(self, symbol: str, period: str = "1mo", interval: str = "1d") -> HistoricalResponse:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        data = [
            HistoricalBar(
                timestamp=index.to_pydatetime(),
                open=float(row.get("Open")),
                high=float(row.get("High")),
                low=float(row.get("Low")),
                close=float(row.get("Close")),
                volume=int(row.get("Volume", 0)),
            )
            for index, row in hist.iterrows()
        ]
        return HistoricalResponse(
            symbol=symbol.upper(),
            interval=interval,
            period=period,
            source=self.name,
            data=data,
        )


class AlphaVantageProvider(StockDataProvider):
    name = "alpha_vantage"

    def _headers(self) -> Dict[str, str]:
        return {"User-Agent": "stock-research-api"}

    def get_quote(self, symbol: str) -> QuoteResponse:
        import requests

        api_key = settings.alpha_vantage_api_key
        if not api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY is not configured.")

        response = requests.get(
            "https://www.alphavantage.co/query",
            params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": api_key},
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        quote = payload.get("Global Quote", {})
        price = float(quote.get("05. price", 0.0))
        previous_close = float(quote.get("08. previous close", 0.0))
        return QuoteResponse(
            symbol=symbol.upper(),
            price=price,
            previous_close=previous_close,
            change=price - previous_close if previous_close else 0.0,
            change_pct=((price - previous_close) / previous_close * 100) if previous_close else 0.0,
            source=self.name,
        )

    def get_historical(self, symbol: str, period: str = "1mo", interval: str = "1d") -> HistoricalResponse:
        raise NotImplementedError("Historical data via Alpha Vantage requires a dedicated implementation and may be added later.")


class FinnhubProvider(StockDataProvider):
    name = "finnhub"

    def get_quote(self, symbol: str) -> QuoteResponse:
        import requests

        api_key = settings.finnhub_api_key
        if not api_key:
            raise ValueError("FINNHUB_API_KEY is not configured.")

        response = requests.get(
            "https://finnhub.io/api/v1/quote",
            params={"symbol": symbol, "token": api_key},
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        price = float(payload.get("c", 0.0))
        previous_close = float(payload.get("pc", 0.0))
        change = price - previous_close if previous_close else 0.0
        change_pct = (change / previous_close * 100) if previous_close else 0.0
        return QuoteResponse(
            symbol=symbol.upper(),
            price=price,
            previous_close=previous_close,
            change=change,
            change_pct=change_pct,
            source=self.name,
        )

    def get_historical(self, symbol: str, period: str = "1mo", interval: str = "1d") -> HistoricalResponse:
        raise NotImplementedError("Historical data via Finnhub requires additional mapping from period to resolution and may be added later.")


class PolygonProvider(StockDataProvider):
    name = "polygon"

    def get_quote(self, symbol: str) -> QuoteResponse:
        import requests

        api_key = settings.polygon_api_key
        if not api_key:
            raise ValueError("POLYGON_API_KEY is not configured.")

        response = requests.get(
            "https://api.polygon.io/v2/last/quote/stocks/{}".format(symbol),
            params={"apiKey": api_key},
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        last = payload.get("results", {})
        price = float(last.get("P", 0.0))
        previous_close = float(last.get("prev", 0.0))
        change = price - previous_close if previous_close else 0.0
        change_pct = (change / previous_close * 100) if previous_close else 0.0
        return QuoteResponse(
            symbol=symbol.upper(),
            price=price,
            previous_close=previous_close,
            change=change,
            change_pct=change_pct,
            source=self.name,
        )

    def get_historical(self, symbol: str, period: str = "1mo", interval: str = "1d") -> HistoricalResponse:
        raise NotImplementedError("Historical data via Polygon requires a date range conversion and may be added later.")


class ProviderFactory:
    @staticmethod
    def create(name: str) -> StockDataProvider:
        provider_name = (name or settings.data_provider).lower()
        providers = {
            "yahoo": YahooFinanceProvider,
            "alpha_vantage": AlphaVantageProvider,
            "finnhub": FinnhubProvider,
            "polygon": PolygonProvider,
        }
        provider_cls = providers.get(provider_name)
        if provider_cls is None:
            raise ValueError(f"Unsupported provider: {provider_name}")
        return provider_cls()
