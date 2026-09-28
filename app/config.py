from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "stock-research-api"
    app_env: str = "development"
    app_debug: bool = True
    data_provider: str = "yahoo"
    alpha_vantage_api_key: str = ""
    finnhub_api_key: str = ""
    polygon_api_key: str = ""
    request_timeout_seconds: int = 10
    cache_db_path: str = "./data/cache.db"
    default_symbols: str = "AAPL,MSFT,NVDA,AMZN,GOOGL"


def _get_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


settings = Settings(
    app_name=os.getenv("APP_NAME", "stock-research-api"),
    app_env=os.getenv("APP_ENV", "development"),
    app_debug=_get_bool(os.getenv("APP_DEBUG"), True),
    data_provider=os.getenv("DATA_PROVIDER", "yahoo").lower(),
    alpha_vantage_api_key=os.getenv("ALPHA_VANTAGE_API_KEY", ""),
    finnhub_api_key=os.getenv("FINNHUB_API_KEY", ""),
    polygon_api_key=os.getenv("POLYGON_API_KEY", ""),
    request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10")),
    cache_db_path=os.getenv("CACHE_DB_PATH", "./data/cache.db"),
    default_symbols=os.getenv("DEFAULT_SYMBOLS", "AAPL,MSFT,NVDA,AMZN,GOOGL"),
)
