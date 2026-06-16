# backend

FastAPI server (Phase 6). Read-only over the precomputed DuckDB store — no LLM
calls in the request path (batch-first). Reuses `ui/data.py` as the query layer
and serves JSON shaped exactly like the frontend's `src/lib/types.ts`.

## Run

```powershell
.\.venv\Scripts\python -m pip install -e ".[api]"   # once
.\.venv\Scripts\python -m uvicorn backend.app.main:app --reload --port 8000
```

Point the API at a different DB with the `REVBENCH_DB` env var (defaults to
`data/revbench.duckdb`). Run it when no batch job is writing (DuckDB single-writer).

## Endpoints

- `GET /api/health`
- `GET /api/universe` — all tickers with their latest recommendation + sparkline prices.
- `GET /api/tickers/{symbol}` — full detail: recommendation, agent signals (with
  reasoning), candlestick bars, scored news, clean quarterly fundamentals.
- `GET /api/cost` — LLM spend summary.

To connect the frontend: replace `frontend/src/lib/mock.ts` with `fetch` calls to
these endpoints (same shapes) and set the API base URL.
