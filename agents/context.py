"""Pure context formatters: DB-shaped data -> compact prompt text.

Kept pure (data in, string out) so they unit-test without a network or a DB.
The orchestrator does the point-in-time DB loading and passes data in.
"""

import pandas as pd

# The indicator columns we surface to the Technical Agent (a readable subset of
# ml/features — the agent interprets, it never recomputes).
TECH_FIELDS = [
    "ret_5", "ret_21", "ret_252_21", "rsi_14", "macd_hist",
    "px_ma50", "px_ma200", "bb_pctb", "vol_21",
]


def technical_context(ticker: str, feature_row: pd.Series, last_close: float) -> str:
    lines = [f"Ticker: {ticker}", f"Last close: {last_close:.2f}", "Indicators:"]
    for field in TECH_FIELDS:
        if field in feature_row and pd.notna(feature_row[field]):
            lines.append(f"  {field} = {feature_row[field]:+.4f}")
    return "\n".join(lines)


def fundamentals_context(ticker: str, facts: pd.DataFrame) -> str:
    """`facts` is already point-in-time filtered (available_at <= as_of)."""
    if facts.empty:
        return f"Ticker: {ticker}\n(no fundamental data available as of this date)"
    lines = [f"Ticker: {ticker}", "Recent quarterly figures (most recent last):"]
    for metric in ("revenue", "net_income", "eps_diluted"):
        sub = facts[facts["metric"] == metric].sort_values("period_end").tail(5)
        if sub.empty:
            continue
        lines.append(f"  {metric}:")
        prev = None
        for row in sub.itertuples():
            period = pd.Timestamp(row.period_end).date()
            yoy = ""
            if prev is not None and prev != 0:
                pct = (row.value - prev) / abs(prev) * 100
                yoy = f" (QoQ {pct:+.1f}%)"
            lines.append(f"    {period}: {row.value:,.0f}{yoy}")
            prev = row.value
    return "\n".join(lines)


def news_context(ticker: str, scored: pd.DataFrame) -> str:
    """`scored` rows: title, score, confidence, event_type, published_at."""
    if scored.empty:
        return f"Ticker: {ticker}\n(no recent scored news)"
    lines = [f"Ticker: {ticker}", "Recent scored headlines (newest first):"]
    for row in scored.itertuples():
        day = pd.Timestamp(row.published_at).date()
        lines.append(
            f"  [{day}] ({row.event_type}, score {row.score:+.2f},"
            f" conf {row.confidence:.2f}) {row.title}"
        )
    return "\n".join(lines)
