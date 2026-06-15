"""Signal fusion (docs/PLAN.md 4.2): ML probability + agent signals -> action.

The ML leg is the backbone (its label IS the 5-day direction we predict); the
agent signals are extra evidence. Combine is a confidence-weighted blend, with
graceful fallback when a leg is missing (a ticker with no agent run is ML-only;
no trained model is agents-only).

NOTE (docs/REVISIT.md R1): this fuses the *latest* snapshot per ticker for the
live recommendation. A walk-forward backtest of whether the agent legs add
alpha needs accumulated history, which doesn't exist yet.
"""

from __future__ import annotations

import pandas as pd

from ..data import load_frames
from ..features.technical import build_dataset
from ..models.lgbm import LGBMSignal
from .schema import FusionConfig, Recommendation

AGENT_LEGS = ("news", "technical", "fundamentals")


def train_and_predict_latest(
    frames: dict[str, pd.DataFrame], seed: int = 42
) -> dict[str, tuple[float, pd.Timestamp]]:
    """Train LGBM on all labeled history, predict P(up) for each ticker's latest row."""
    X, y = build_dataset(frames)
    mask = y.notna()
    model = LGBMSignal(seed=seed)
    model.fit(X[mask], y[mask])

    latest = X.groupby(level="ticker").tail(1)  # X is date-sorted -> last = newest
    proba = model.predict_proba_up(latest)
    out: dict[str, tuple[float, pd.Timestamp]] = {}
    for (day, ticker), p in zip(latest.index, proba, strict=True):
        out[ticker] = (float(p), day)
    return out


def fuse(
    ticker: str,
    as_of_date,
    ml_proba: float | None,
    agent_signals: dict[str, tuple[float, float]],  # agent -> (signal, confidence)
    config: FusionConfig | None = None,
) -> Recommendation:
    config = config or FusionConfig()
    components: dict[str, float] = {}
    legs: list[tuple[float, float]] = []  # (signal, weight)

    if ml_proba is not None:
        ml_signal = (ml_proba - 0.5) * 2  # [0,1] -> [-1,1]
        components["ml"] = ml_signal
        legs.append((ml_signal, config.ml_weight))

    # agent consensus: confidence-weighted mean of available agent legs
    agent_pairs = [(s, c) for s, c in agent_signals.values() if c > 0]
    for name, (s, _c) in agent_signals.items():
        components[name] = s
    if agent_pairs:
        wsum = sum(c for _s, c in agent_pairs)
        consensus = sum(s * c for s, c in agent_pairs) / wsum
        legs.append((consensus, config.agent_weight))

    if not legs:
        score, confidence = 0.0, 0.0
    else:
        total_w = sum(w for _s, w in legs)
        score = sum(s * w for s, w in legs) / total_w
        # confidence: magnitude of the net view, dampened when legs disagree
        signals = [s for s, _w in legs]
        agreement = 1.0 - (max(signals) - min(signals)) / 2 if len(signals) > 1 else 1.0
        confidence = round(min(abs(score) * agreement * 2, 1.0), 3)

    if score >= config.buy_threshold:
        action = "buy"
    elif score <= config.sell_threshold:
        action = "sell"
    else:
        action = "hold"

    return Recommendation(
        ticker=ticker,
        as_of_date=as_of_date,
        action=action,
        score=round(score, 3),
        confidence=confidence,
        ml_proba=ml_proba,
        components={k: round(v, 3) for k, v in components.items()},
        rationale=_rationale(action, components),
    )


def _rationale(action: str, components: dict[str, float]) -> str:
    """Deterministic template. The Strategist Agent (PLAN 4.4) will replace this
    with prose once built (docs/REVISIT.md — Phase 4 remaining)."""
    parts = []
    if "ml" in components:
        parts.append(f"ML model leans {_word(components['ml'])} ({components['ml']:+.2f})")
    agent_bits = [f"{k} {components[k]:+.2f}" for k in AGENT_LEGS if k in components]
    if agent_bits:
        parts.append("agents: " + ", ".join(agent_bits))
    head = {"buy": "Net bullish", "sell": "Net bearish", "hold": "No clear edge"}[action]
    return f"{head}. " + "; ".join(parts) + "."


def _word(signal: float) -> str:
    if signal > 0.15:
        return "bullish"
    if signal < -0.15:
        return "bearish"
    return "neutral"


def generate_recommendations(
    db_path,
    agent_store,
    tickers: tuple[str, ...],
    config: FusionConfig | None = None,
) -> list[Recommendation]:
    """End-to-end: train ML on history, pull latest agent signals, fuse per ticker."""
    frames = load_frames(db_path, tickers)
    if not frames:
        return []
    ml = train_and_predict_latest(frames)

    recs: list[Recommendation] = []
    for ticker in tickers:
        if ticker not in ml:
            continue
        proba, day = ml[ticker]
        signals = {
            s["agent"]: (s["signal"], s["confidence"])
            for s in agent_store_signals(agent_store, ticker)
        }
        recs.append(fuse(ticker, day.date(), proba, signals, config))
    return recs


def agent_store_signals(agent_store, ticker: str) -> list[dict]:
    """Latest agent_signals rows for a ticker as plain dicts (decouples fuse from
    the store's row type; the store returns a DataFrame)."""
    df = agent_store.load_signals(ticker)
    if df.empty:
        return []
    latest = df[df["as_of_date"] == df["as_of_date"].max()]
    return [
        {"agent": r.agent, "signal": float(r.signal), "confidence": float(r.confidence)}
        for r in latest.itertuples()
    ]
