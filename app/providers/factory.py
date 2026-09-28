from __future__ import annotations

from app.config import settings
from app.providers.base import (  # noqa: F401
    AlphaVantageProvider,
    FinnhubProvider,
    PolygonProvider,
    StockDataProvider,
    YahooFinanceProvider,
)


class ProviderFactory:
    @staticmethod
    def create(name: str | None = None):
        provider_name = (name or settings.data_provider).lower()
        registry = {
            "yahoo": YahooFinanceProvider,
            "alpha_vantage": AlphaVantageProvider,
            "finnhub": FinnhubProvider,
            "polygon": PolygonProvider,
        }
        provider_class = registry.get(provider_name)
        if provider_class is None:
            raise ValueError(f"Unsupported provider: {provider_name}")
        return provider_class()


__all__ = [
    "ProviderFactory",
    "StockDataProvider",
    "YahooFinanceProvider",
    "AlphaVantageProvider",
    "FinnhubProvider",
    "PolygonProvider",
]
