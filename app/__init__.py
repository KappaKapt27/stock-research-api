from fastapi import FastAPI

app = FastAPI(
    title="Research-Only Stock Analysis API",
    version="0.1.0",
    description=(
        "A research-only stock analysis API for educational and data analysis use. "
        "This service does not trade, place orders, or connect to brokerage accounts."
    ),
)
