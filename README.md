# Research-Only Stock Analysis API

This project is a research-oriented Python API for stock market analysis. It is designed for educational and research use only and does not place orders, execute trades, or interact with brokerage accounts such as Robinhood.

## Purpose

- Query market data and historical prices from public data providers
- Compute technical signal summaries for research review
- Provide a small API for portfolio/watchlist workflows
- Keep all logic clearly non-trading and non-executing

## Important notice

This project is not a trading bot, not a live brokerage integration, and not meant to automate order placement. It is explicitly designed as a research-only workflow.

## Features

- FastAPI service with async endpoints
- Provider abstraction with support for multiple public data sources
- Quote and historical price endpoints
- Technical signal summary generation (RSI, SMA, volatility, price vs moving averages)
- Watchlist aggregation
- Environment-based configuration

## Supported providers

The app is structured to support verified public providers, including:

- Yahoo Finance
- Alpha Vantage
- Finnhub
- Polygon

The active provider can be selected with the `DATA_PROVIDER` environment variable.

## Quick start

1. Create a virtual environment
2. Install dependencies
3. Copy `.env.example` to `.env` and set your keys as needed
4. Run the app

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Environment variables

See `.env.example` for the full list.

## API endpoints

- `GET /health` — health check
- `GET /providers` — list configured providers and status
- `GET /quote/{symbol}` — latest quote summary
- `GET /historical/{symbol}` — historical price data
- `GET /signals/{symbol}` — technical signal summary
- `GET /watchlist?symbols=AAPL,MSFT` — combined quote summary for multiple symbols

## Example

```bash
curl http://localhost:8000/quote/AAPL
curl "http://localhost:8000/historical/AAPL?period=1mo&interval=1d"
curl http://localhost:8000/signals/MSFT
```

## Safety and compliance

- No brokerage connections
- No order placement logic
- No guaranteed profit claims
- Research-only design

## License

MIT
