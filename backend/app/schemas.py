"""Response models. Field names match the frontend's src/lib/types.ts exactly,
so swapping the mock layer for these endpoints is a one-file change there.
"""

from pydantic import BaseModel


class Stock(BaseModel):
    ticker: str
    name: str
    sector: str


class Bar(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float


class Components(BaseModel):
    ml: float
    news: float
    technical: float
    fundamentals: float


class AgentSignal(BaseModel):
    agent: str
    signal: float
    confidence: float
    regime: str | None = None
    valuation_view: str | None = None
    growth_view: str | None = None
    rationale: str | None = None
    summary: str | None = None
    key_events: list[str] | None = None
    catalysts: list[str] | None = None
    red_flags: list[str] | None = None


class NewsItem(BaseModel):
    date: str
    title: str
    score: float
    confidence: float
    event_type: str


class FundamentalRow(BaseModel):
    metric: str
    period_end: str
    value: float
    yoy: float | None
    isEps: bool


class Recommendation(BaseModel):
    ticker: str
    asOf: str
    action: str
    score: float
    confidence: float
    mlProba: float
    components: Components
    riskLevel: str
    maxPositionPct: float
    stopLossPct: float | None
    riskFlags: list[str]
    thesis: str
    counterarguments: list[str]
    conviction: str


class TickerSummary(BaseModel):
    stock: Stock
    rec: Recommendation
    prices: list[Bar]  # short series for the sparkline
    lastClose: float
    change1d: float


class TickerDetail(BaseModel):
    stock: Stock
    rec: Recommendation
    signals: list[AgentSignal]
    prices: list[Bar]
    news: list[NewsItem]
    fundamentals: list[FundamentalRow]
    lastClose: float
    change1d: float


class CostSummary(BaseModel):
    today: float
    total: float
    calls: int
