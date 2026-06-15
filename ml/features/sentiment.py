"""News-sentiment feature + Information Coefficient (docs/PLAN.md 4.5, 2.2).

This is the one agent-derived signal with real (if short) history, so it's the
only piece of the "do agents add alpha?" question we can measure today.

Point-in-time (docs/REVISIT.md R3): the stored sentiment row's `available_at`
is the batch compute time, which is wrong for a backtest. But the score is a
deterministic function of the article text (temp=0), so its true availability is
publication time. We therefore derive the feature from the article's
`published_at`, and to avoid any same-day leak the feature at date t uses only
articles published strictly before t.

⚠️ News history is ~1 month deep (docs/REVISIT.md R2), so any IC here is
INDICATIVE, not conclusive — always report it next to the sample size.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from data_pipeline.store import DEFAULT_DB_PATH
from data_pipeline.universe import HORIZON_DAYS

from ..data import load_frames


def load_scored_news(db_path: str | Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """(ticker, published_at, score, confidence) for every scored article."""
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        return con.execute(
            """
            SELECT s.ticker, n.published_at, s.score, s.confidence
            FROM news_sentiment s
            JOIN news n ON n.id = s.news_id AND n.ticker = s.ticker
            """
        ).fetchdf()
    finally:
        con.close()


def daily_sentiment(
    scored: pd.DataFrame, window_days: int = 5, index: pd.DatetimeIndex | None = None
) -> pd.DataFrame:
    """Feature panel (date x ticker): trailing confidence-weighted mean sentiment.

    The value at date t aggregates articles published in [t-window, t-1] — strictly
    before t, so the feature is usable for a decision made at close(t). `index`
    sets the calendar days to compute over; default spans the article dates plus
    one window (so the last article is fully realized).
    """
    if scored.empty:
        return pd.DataFrame()
    df = scored.copy()
    df["day"] = pd.to_datetime(df["published_at"]).dt.normalize()
    df["wscore"] = df["score"] * df["confidence"]

    per_day = df.groupby(["day", "ticker"]).agg(
        wscore=("wscore", "sum"), conf=("confidence", "sum")
    )
    daily = (per_day["wscore"] / per_day["conf"].clip(lower=1e-9)).unstack("ticker")

    if index is None:
        index = pd.date_range(
            daily.index.min(), daily.index.max() + pd.Timedelta(days=window_days), freq="D"
        )
    daily = daily.reindex(index)
    # trailing window, then shift(1) so date t sees only strictly-earlier articles
    return daily.rolling(window_days, min_periods=1).mean().shift(1)


def _forward_returns(
    frames: dict[str, pd.DataFrame], horizon: int = HORIZON_DAYS
) -> pd.DataFrame:
    cols = {}
    for ticker, f in frames.items():
        c = f["adj_close"]
        cols[ticker] = c.shift(-horizon) / c - 1.0
    return pd.DataFrame(cols)


def sentiment_ic(
    db_path: str | Path = DEFAULT_DB_PATH,
    horizon: int = HORIZON_DAYS,
    window_days: int = 5,
) -> dict:
    """Spearman IC of the sentiment feature vs forward returns, with sample size."""
    scored = load_scored_news(db_path)
    feat = daily_sentiment(scored, window_days)
    if feat.empty:
        return {"ic": float("nan"), "n": 0, "note": "no scored news"}

    frames = load_frames(db_path)
    fwd = _forward_returns(frames, horizon)

    # align on common dates/tickers; feature index is calendar, returns are trading days
    common_t = [t for t in feat.columns if t in fwd.columns]
    pairs_f, pairs_r = [], []
    for ticker in common_t:
        joined = pd.concat(
            [feat[ticker].rename("f"), fwd[ticker].rename("r")], axis=1
        ).dropna()
        pairs_f.append(joined["f"])
        pairs_r.append(joined["r"])
    if not pairs_f:
        return {"ic": float("nan"), "n": 0, "note": "no overlap"}

    f = pd.concat(pairs_f)
    r = pd.concat(pairs_r)
    n = len(f)
    ic = float(f.corr(r, method="spearman")) if n > 2 else float("nan")
    return {
        "ic": ic,
        "n": n,
        "horizon": horizon,
        "window_days": window_days,
        "date_range": (str(feat.index.min().date()), str(feat.index.max().date())),
    }


def main() -> int:
    """python -m ml.features.sentiment -- print the (indicative) sentiment IC."""
    result = sentiment_ic()
    print("News-sentiment Information Coefficient (Spearman) vs forward returns")
    print(f"  IC          : {result['ic']:.4f}")
    print(f"  sample size : {result['n']}")
    if result["n"]:
        print(f"  horizon     : {result.get('horizon')}d, window {result.get('window_days')}d")
        print(f"  date range  : {result.get('date_range')}")
        print("\n  [!] INDICATIVE ONLY -- news history is ~1 month (docs/REVISIT.md R2).")
    else:
        print("\n  [!] NOT MEASURABLE YET (n=0). All scored news is more recent than the")
        print("      last date with a computable 5-day forward return (prices end before")
        print("      the news gets its forward window). This is docs/REVISIT.md R1/R2 in")
        print("      action: let the scheduler run so prices advance past the news dates,")
        print("      then the IC becomes computable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
