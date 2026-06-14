"""RevBench temporary dashboard (docs/DECISIONS.md D5 — Streamlit, internal/temp).

Read-only view over the precomputed DuckDB store: agent signals, the reasoning
trail (the product differentiator), prices, sentiment-scored news, fundamentals.
No LLM calls here — everything was computed by the batch.

Run:  streamlit run ui/streamlit_app.py
Replaced by the Next.js app in Phase 7.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui import data

DISCLAIMER = (
    "⚠️ **Not financial advice.** RevBench is a student research project "
    "(INSA Lyon 4IF). Signals are experimental and unvalidated. Do not trade on this."
)


def _signal_color(value: float) -> str:
    if value > 0.15:
        return "#1a7f37"  # green
    if value < -0.15:
        return "#cf222e"  # red
    return "#8b949e"  # grey / neutral


def _signal_bg(value: float) -> str:
    """Red→green cell background by signal magnitude (matplotlib-free)."""
    if pd.isna(value):
        return ""
    alpha = min(abs(value), 1.0) * 0.55
    rgb = "26,127,55" if value >= 0 else "207,34,46"  # green / red
    return f"background-color: rgba({rgb},{alpha:.2f})"


def render_overview(db: str) -> None:
    st.subheader("Latest agent signals across the universe")
    matrix = data.latest_signal_matrix(db)
    if matrix.empty:
        st.info("No agent signals yet. Run:  `python -m agents.run --task signals`")
        return
    matrix.insert(0, "avg", matrix.mean(axis=1))
    styled = matrix.style.format("{:+.2f}", na_rep="—").map(_signal_bg)
    st.dataframe(styled, width="stretch")
    st.caption(
        "Raw per-agent signals in [-1, 1] (bearish → bullish over ~5 trading days). "
        "`avg` is a naive mean — the learned fusion comes in Phase 4, not a recommendation yet."
    )


def render_price_chart(db: str, ticker: str) -> None:
    prices = data.price_history(db, ticker, days=180)
    if prices.empty:
        st.info("No price history.")
        return
    fig = go.Figure(
        go.Candlestick(
            x=prices.index,
            open=prices["open"], high=prices["high"],
            low=prices["low"], close=prices["close"],
            name=ticker,
        )
    )
    fig.update_layout(
        height=360, margin=dict(l=0, r=0, t=10, b=0),
        xaxis_rangeslider_visible=False, showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")


def render_agent_insights(signals: list[dict]) -> None:
    st.subheader("Agent insights")
    if not signals:
        st.info("No agent run for this ticker yet. Run:  "
                "`python -m agents.run --task signals --tickers " "<TICKER>`")
        return

    cols = st.columns(len(signals))
    for col, s in zip(cols, signals, strict=True):
        color = _signal_color(s["signal"])
        col.markdown(
            f"**{s['agent'].title()}**<br>"
            f"<span style='font-size:1.6em;color:{color}'>{s['signal']:+.2f}</span>"
            f"<br><span style='color:#8b949e'>conf {s['confidence']:.2f}</span>",
            unsafe_allow_html=True,
        )

    for s in signals:
        p = s["payload"]
        with st.expander(f"{s['agent'].title()} — reasoning", expanded=(s["agent"] == "news")):
            if "rationale" in p:
                st.write(p["rationale"])
            if "summary" in p:
                st.write(p["summary"])
            for field in ("regime", "valuation_view", "growth_view"):
                if field in p:
                    st.caption(f"{field}: **{p[field]}**")
            for field in ("key_events", "catalysts", "red_flags"):
                if p.get(field):
                    st.markdown(f"**{field.replace('_', ' ').title()}**")
                    for item in p[field]:
                        st.markdown(f"- {item}")


def render_news(db: str, ticker: str) -> None:
    st.subheader("Recent scored news")
    news = data.ticker_news(db, ticker, limit=15)
    if news.empty:
        st.info("No scored news.")
        return
    news = news.copy()
    news["published_at"] = pd.to_datetime(news["published_at"]).dt.date
    st.dataframe(
        news.rename(columns={"published_at": "date"}),
        width="stretch", hide_index=True,
    )


def render_fundamentals(db: str, ticker: str) -> None:
    facts = data.ticker_fundamentals(db, ticker)
    if facts.empty:
        return
    st.subheader("Fundamentals (SEC EDGAR)")
    facts = facts.copy()
    facts["period_end"] = pd.to_datetime(facts["period_end"]).dt.date
    st.dataframe(
        facts[["metric", "period_end", "value", "form"]],
        width="stretch", hide_index=True,
    )


def render_ticker(db: str, ticker: str) -> None:
    st.header(f"{ticker} — {data.stock_name(ticker)}")
    st.caption(data.sector(ticker))

    prices = data.price_history(db, ticker, days=180)
    if not prices.empty:
        last = prices.iloc[-1]
        prev = prices.iloc[-2] if len(prices) > 1 else last
        change = (last["adj_close"] / prev["adj_close"] - 1) * 100
        c1, c2 = st.columns(2)
        c1.metric("Last close", f"${last['close']:.2f}", f"{change:+.2f}%")
        c2.metric("As of", str(prices.index[-1].date()))

    render_price_chart(db, ticker)
    render_agent_insights(data.ticker_signals(db, ticker))
    render_news(db, ticker)
    render_fundamentals(db, ticker)


def main() -> None:
    st.set_page_config(page_title="RevBench", page_icon="📈", layout="wide")
    st.title("📈 RevBench")
    st.warning(DISCLAIMER)

    db = str(data.DEFAULT_DB_PATH)
    tickers = data.available_tickers(db)

    with st.sidebar:
        st.header("Navigation")
        view = st.radio("View", ["Overview", *tickers], index=0)
        st.divider()
        cost = data.cost_summary(db)
        st.metric("LLM spend today", f"${cost['today']:.4f}")
        st.caption(f"All-time: ${cost['total']:.4f} over {cost['calls']} calls")

    if not tickers:
        st.info("No data yet. Run `python -m data_pipeline.fetch --all --years 5` first.")
        return

    if view == "Overview":
        render_overview(db)
    else:
        render_ticker(db, view)


if __name__ == "__main__":
    main()
