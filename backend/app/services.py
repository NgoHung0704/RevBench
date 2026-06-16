"""Assemble API responses from the read layer (ui.data) — read-only, no LLM."""

from __future__ import annotations

import duckdb
import pandas as pd

from data_pipeline.fundamentals.normalize import quarterly_series
from data_pipeline.universe import STOCK_BY_TICKER, TICKERS
from ui import data as ui

from . import schemas


def _bars(db: str, ticker: str, days: int) -> list[schemas.Bar]:
    df = ui.price_history(db, ticker, days=days)
    out = []
    for ts, row in df.iterrows():
        out.append(
            schemas.Bar(
                time=pd.Timestamp(ts).date().isoformat(),
                open=float(row["open"]), high=float(row["high"]),
                low=float(row["low"]), close=float(row["close"]),
            )
        )
    return out


def _recommendation(rec: dict, ticker: str) -> schemas.Recommendation:
    """Map the read-layer dict to the API model, with fallbacks for the rows that
    haven't been enriched by the Risk/Strategist agents yet."""
    comp = rec.get("components") or {}
    return schemas.Recommendation(
        ticker=ticker,
        asOf=str(rec["as_of_date"]),
        action=rec["action"],
        score=rec["score"],
        confidence=rec["confidence"],
        mlProba=rec["ml_proba"] if rec["ml_proba"] is not None else 0.5,
        components=schemas.Components(
            ml=comp.get("ml", 0.0), news=comp.get("news", 0.0),
            technical=comp.get("technical", 0.0), fundamentals=comp.get("fundamentals", 0.0),
        ),
        riskLevel=rec.get("risk_level") or "unrated",
        maxPositionPct=rec.get("max_position_pct") or 0.0,
        stopLossPct=rec.get("stop_loss_pct"),
        riskFlags=rec.get("risk_flags") or [],
        thesis=rec.get("thesis") or rec.get("rationale") or "",
        counterarguments=rec.get("counterarguments") or [],
        conviction=rec.get("conviction") or "low",
    )


def _signals(db: str, ticker: str) -> list[schemas.AgentSignal]:
    out = []
    for s in ui.ticker_signals(db, ticker):
        p = s["payload"]
        out.append(
            schemas.AgentSignal(
                agent=s["agent"], signal=s["signal"], confidence=s["confidence"],
                regime=p.get("regime"), valuation_view=p.get("valuation_view"),
                growth_view=p.get("growth_view"), rationale=p.get("rationale"),
                summary=p.get("summary"), key_events=p.get("key_events"),
                catalysts=p.get("catalysts"), red_flags=p.get("red_flags"),
            )
        )
    return out


def _news(db: str, ticker: str) -> list[schemas.NewsItem]:
    df = ui.ticker_news(db, ticker, limit=12)
    return [
        schemas.NewsItem(
            date=pd.Timestamp(r["published_at"]).date().isoformat(),
            title=r["title"], score=float(r["score"]),
            confidence=float(r["confidence"]), event_type=r["event_type"],
        )
        for _, r in df.iterrows()
    ]


def _fundamentals(db: str, ticker: str) -> list[schemas.FundamentalRow]:
    """Clean quarterly series per metric (docs/REVISIT.md R4), read-only."""
    con = duckdb.connect(db, read_only=True)
    try:
        facts = con.execute(
            "SELECT metric, period_start, period_end, value, filed "
            "FROM fundamentals WHERE ticker = ?",
            [ticker],
        ).fetchdf()
    except Exception:
        return []
    finally:
        con.close()
    if facts.empty:
        return []
    rows: list[schemas.FundamentalRow] = []
    for metric in ("revenue", "net_income", "eps_diluted"):
        series = quarterly_series(facts[facts["metric"] == metric]).tail(6)
        for r in series.itertuples():
            rows.append(
                schemas.FundamentalRow(
                    metric=metric,
                    period_end=pd.Timestamp(r.period_end).date().isoformat(),
                    value=float(r.value),
                    yoy=None if pd.isna(r.yoy) else float(r.yoy),
                    isEps=metric == "eps_diluted",
                )
            )
    return rows


def _change(bars: list[schemas.Bar]) -> tuple[float, float]:
    if not bars:
        return 0.0, 0.0
    last = bars[-1].close
    prev = bars[-2].close if len(bars) > 1 else last
    return last, (last - prev) / prev if prev else 0.0


def universe(db: str) -> list[schemas.TickerSummary]:
    out = []
    for ticker in TICKERS:
        rec = ui.ticker_recommendation(db, ticker)
        if rec is None:
            continue
        stock = STOCK_BY_TICKER[ticker]
        bars = _bars(db, ticker, 45)
        last, chg = _change(bars)
        out.append(
            schemas.TickerSummary(
                stock=schemas.Stock(ticker=stock.ticker, name=stock.name, sector=stock.sector),
                rec=_recommendation(rec, ticker),
                prices=bars, lastClose=last, change1d=chg,
            )
        )
    out.sort(key=lambda s: s.rec.score, reverse=True)
    return out


def ticker_detail(db: str, symbol: str) -> schemas.TickerDetail | None:
    ticker = symbol.upper()
    rec = ui.ticker_recommendation(db, ticker)
    if rec is None or ticker not in STOCK_BY_TICKER:
        return None
    stock = STOCK_BY_TICKER[ticker]
    bars = _bars(db, ticker, 180)
    last, chg = _change(bars)
    return schemas.TickerDetail(
        stock=schemas.Stock(ticker=stock.ticker, name=stock.name, sector=stock.sector),
        rec=_recommendation(rec, ticker),
        signals=_signals(db, ticker),
        prices=bars,
        news=_news(db, ticker),
        fundamentals=_fundamentals(db, ticker),
        lastClose=last, change1d=chg,
    )


def cost(db: str) -> schemas.CostSummary:
    c = ui.cost_summary(db)
    return schemas.CostSummary(today=c["today"], total=c["total"], calls=c["calls"])
