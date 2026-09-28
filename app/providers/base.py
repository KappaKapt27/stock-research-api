from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List

import requests

from app.config import settings
from app.schemas import HistoricalBar, HistoricalResponse, QuoteResponse


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
                open=float(row.get("Open", 0.0)),
                high=float(row.get("High", 0.0)),
                low=float(row.get("Low", 0.0)),
                close=float(row.get("Close", 0.0)),
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

    def get_quote(self, symbol: str) -> QuoteResponse:
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
        api_key = settings.alpha_vantage_api_key
        if not api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY is not configured.")

        response = requests.get(
            "https://www.alphavantage.co/query",
            params={
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": "compact" if "1mo" in period or "3mo" in period else "full",
                "apikey": api_key,
            },
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        series = payload.get("Time Series (Daily)", {})
        data = []
        for timestamp, values in series.items():
            data.append(
                HistoricalBar(
                    timestamp=datetime.fromisoformat(timestamp),
                    open=float(values.get("1. open", 0.0)),
                    high=float(values.get("2. high", 0.0)),
                    low=float(values.get("3. low", 0.0)),
                    close=float(values.get("4. close", 0.0)),
                    volume=int(values.get("5. volume", 0)),
                )
            )
        data = sorted(data, key=lambda x: x.timestamp or datetime.min)
        return HistoricalResponse(
            symbol=symbol.upper(),
            interval=interval,
            period=period,
            source=self.name,
            data=data[-250:],
        )


class FinnhubProvider(StockDataProvider):
    name = "finnhub"

    def get_quote(self, symbol: str) -> QuoteResponse:
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
        api_key = settings.finnhub_api_key
        if not api_key:
            raise ValueError("FINNHUB_API_KEY is not configured.")

        resolution = "D" if interval in {"1d", "1wk"} else "1"
        response = requests.get(
            "https://finnhub.io/api/v1/stock/candle",
            params={
                "symbol": symbol,
                "resolution": resolution,
                "token": api_key,
                "from": 0,
                "to": int(datetime.utcnow().timestamp()),
            },
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        data = []
        for index, ts in enumerate(payload.get("t", [])):
            data.append(
                HistoricalBar(
                    timestamp=datetime.utcfromtimestamp(ts),
                    open=float(payload.get("o", [0.0])[index]),
                    high=float(payload.get("h", [0.0])[index]),
                    low=float(payload.get("l", [0.0])[index]),
                    close=float(payload.get("c", [0.0])[index]),
                    volume=int(payload.get("v", [0])[index]),
                )
            )
        return HistoricalResponse(
            symbol=symbol.upper(),
            interval=interval,
            period=period,
            source=self.name,
            data=data,
        )


class PolygonProvider(StockDataProvider):
    name = "polygon"

    def get_quote(self, symbol: str) -> QuoteResponse:
        api_key = settings.polygon_api_key
        if not api_key:
            raise ValueError("POLYGON_API_KEY is not configured.")

        response = requests.get(
            f"https://api.polygon.io/v2/last/quote/stocks/{symbol}",
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
        api_key = settings.polygon_api_key
        if not api_key:
            raise ValueError("POLYGON_API_KEY is not configured.")

        to_date = datetime.utcnow().strftime("%Y-%m-%d")
        from_date = (datetime.utcnow().replace(month=1) if period.startswith("1y") else datetime.utcnow()).strftime("%Y-%m-%d")
        response = requests.get(
            f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{from_date}/{to_date}",
            params={"apiKey": api_key, "limit": 5000},
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        data = []
        for item in payload.get("results", []):
            data.append(
                HistoricalBar(
                    timestamp=datetime.utcfromtimestamp(item.get("t", 0) / 1000),
                    open=float(item.get("o", 0.0)),
                    high=float(item.get("h", 0.0)),
                    low=float(item.get("l", 0.0)),
                    close=float(item.get("c", 0.0)),
                    volume=int(item.get("v", 0)),
                )
            )
        return HistoricalResponse(
            symbol=symbol.upper(),
            interval=interval,
            period=period,
            source=self.name,
            data=sorted(data, key=lambda x: x.timestamp or datetime.min),
        )
