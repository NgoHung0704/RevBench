"""RevBench API (docs/PLAN.md Phase 6).

Read-only HTTP over the precomputed DuckDB store — no LLM calls in the request
path (batch-first). The frontend swaps its mock layer for these endpoints.

Run: uvicorn backend.app.main:app --reload  (needs the `.[api]` extra)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import schemas, services
from .config import ALLOWED_ORIGINS, db_path

app = FastAPI(
    title="RevBench API",
    version="0.1.0",
    description="AI decision support for blue-chip stocks. Not financial advice.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "disclaimer": "Not financial advice."}


@app.get("/api/universe", response_model=list[schemas.TickerSummary])
def get_universe():
    return services.universe(db_path())


@app.get("/api/cost", response_model=schemas.CostSummary)
def get_cost():
    return services.cost(db_path())


@app.get("/api/tickers/{symbol}", response_model=schemas.TickerDetail)
def get_ticker(symbol: str):
    detail = services.ticker_detail(db_path(), symbol)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"no data for {symbol}")
    return detail
