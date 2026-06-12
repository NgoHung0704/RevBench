"""Stock universe for RevBench (docs/DECISIONS.md D9 — closed 2026-06-12).

15 blue-chip US tickers tradable on Revolut: liquid, sector-diverse.
Prediction target: direction over a 5-trading-day horizon (classification).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Stock:
    ticker: str
    name: str
    sector: str


UNIVERSE: tuple[Stock, ...] = (
    Stock("AAPL", "Apple", "Technology"),
    Stock("MSFT", "Microsoft", "Technology"),
    Stock("NVDA", "NVIDIA", "Semiconductors"),
    Stock("GOOGL", "Alphabet", "Communication Services"),
    Stock("AMZN", "Amazon", "Consumer Discretionary"),
    Stock("META", "Meta Platforms", "Communication Services"),
    Stock("TSLA", "Tesla", "Consumer Discretionary"),
    Stock("JPM", "JPMorgan Chase", "Financials"),
    Stock("V", "Visa", "Financials"),
    Stock("MA", "Mastercard", "Financials"),
    Stock("KO", "Coca-Cola", "Consumer Staples"),
    Stock("PG", "Procter & Gamble", "Consumer Staples"),
    Stock("JNJ", "Johnson & Johnson", "Healthcare"),
    Stock("XOM", "Exxon Mobil", "Energy"),
    Stock("DIS", "Walt Disney", "Communication Services"),
)

TICKERS: tuple[str, ...] = tuple(s.ticker for s in UNIVERSE)

STOCK_BY_TICKER: dict[str, Stock] = {s.ticker: s for s in UNIVERSE}

HORIZON_DAYS = 5
