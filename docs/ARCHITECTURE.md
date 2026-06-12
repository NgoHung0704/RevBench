# RevBench — Kiến trúc hệ thống

## Sơ đồ tổng thể

```
                        ┌────────────────────────────────────────────┐
   NGUỒN DỮ LIỆU        │              DATA PIPELINE                 │
                        │            (data_pipeline/)                │
 Prices (yfinance/…) ──▶│  ingestion ──▶ validation ──▶ storage      │
 News (RSS/GDELT)    ──▶│       mọi bản ghi có `available_at`        │
 Fundamentals (EDGAR)──▶│                                            │
 Alt-data (Trends,   ──▶│   Storage: DuckDB/Parquet (research)       │
  Reddit, StockTwits)   │            PostgreSQL (serving, từ P6)     │
                        └──────────────┬─────────────────────────────┘
                                       │
                ┌──────────────────────┼──────────────────────┐
                ▼                      ▼                      │
   ┌─────────────────────┐  ┌─────────────────────┐           │
   │      ML LAYER       │  │    AGENT LAYER      │           │
   │       (ml/)         │  │     (agents/)       │           │
   │ features ─▶ LightGBM│  │ Orchestrator        │           │
   │ walk-forward        │  │  ├─ News Agent      │◀─ Claude API
   │ backtest engine     │  │  ├─ Sentiment Agent │   (tool use, web search,
   │                     │  │  ├─ Technical Agent │    batch, caching)
   │  ml_signal(t,d)     │  │  ├─ Fundamentals Ag.│           │
   └─────────┬───────────┘  │  ├─ AltData Agent   │           │
             │              │  ├─ Risk Agent      │           │
             │              │  └─ Strategist Ag.  │           │
             │              │  agent_signals(t,d) │           │
             │              └─────────┬───────────┘           │
             │                        │                       │
             ▼                        ▼                       │
   ┌──────────────────────────────────────────────┐           │
   │           SIGNAL FUSION (ml/fusion)          │           │
   │  ensemble(ml_signal, agent_signals) ─▶       │           │
   │  Recommendation{action, confidence,          │           │
   │     horizon, rationale, risk}                │           │
   └─────────────────────┬────────────────────────┘           │
                         │  ghi vào DB                        │
                         ▼                                    │
   ┌──────────────────────────────────────────────┐           │
   │         BACKEND API (backend/, FastAPI)      │           │
   │  REST + SSE  — chỉ ĐỌC kết quả tính sẵn      │           │
   └─────────────────────┬────────────────────────┘           │
                         ▼                                    │
   ┌──────────────────────────────────────────────┐           │
   │      FRONTEND (frontend/, Next.js)           │           │
   │  Dashboard / Ticker / Agent insights /       │           │
   │  Strategy + disclaimer                       │           │
   └──────────────────────────────────────────────┘           │
                                                              │
   SCHEDULER (APScheduler): daily 22:30 CET ──────────────────┘
   pipeline ▶ ml predict ▶ agents ▶ fusion ▶ notify
```

## Nguyên tắc kiến trúc

1. **Batch-first.** Mọi thứ đắt (LLM, ML inference) chạy theo lịch sau giờ đóng cửa thị trường Mỹ. Web app chỉ đọc kết quả — phản hồi tức thì, chi phí dự đoán được, không bao giờ gọi LLM theo request người dùng.
2. **Point-in-time correctness.** Mọi bảng có cột `available_at`. Backtest chỉ được nhìn dữ liệu có `available_at <= t`. Đây là phòng tuyến chống lookahead bias — vi phạm là kết quả nghiên cứu vô nghĩa.
3. **Agents diễn giải, code tính toán.** LLM không bao giờ tự tính RSI hay trung bình — số liệu do `ml/features` tính, agent nhận số và *diễn giải/suy luận*. LLM giỏi ngôn ngữ & tổng hợp, kém số học.
4. **Mọi signal đều được lưu lịch sử** (kể cả agent output) → agent signals backtest được như feature thường, trả lời được câu hỏi "agents có thêm alpha không?".
5. **Provider abstraction.** `PriceProvider`, `NewsProvider` là interface — nguồn miễn phí chết thì thay adapter, không chạm logic.

## Cấu trúc thư mục (mục tiêu)

```
RevBench/
├── data_pipeline/          # ingestion + validation + storage adapters
│   ├── providers/          #   yfinance_provider.py, finnhub_provider.py, ...
│   ├── news/               #   rss.py, gdelt.py, reddit.py, stocktwits.py
│   ├── store.py            #   DuckDB/Postgres adapters
│   └── jobs.py             #   các job cho scheduler
├── ml/
│   ├── features/           #   technical, calendar, news-derived features
│   ├── models/             #   lgbm.py, baselines.py, (lstm.py)
│   ├── backtest/           #   walk-forward harness, metrics.py
│   └── fusion/             #   ensemble ML + agent signals
├── agents/
│   ├── orchestrator.py     #   fan-out/gather, cost guard
│   ├── roster/             #   news.py, sentiment.py, technical.py, ...
│   ├── schemas.py          #   Pydantic schemas cho structured outputs
│   └── prompts/            #   system prompts (version-controlled)
├── backend/
│   └── app/                #   FastAPI: routers, services, db
├── frontend/               #   Next.js app
├── notebooks/              #   nghiên cứu, EDA — không import vào production code
├── tests/
└── docs/                   #   tài liệu này
```

## Luồng daily (khi hoàn chỉnh)

```
22:30 CET  Scheduler tick (sau khi NYSE đóng 22:00 CET)
  1. data_pipeline: tải giá EOD, tin trong ngày, alt-data        (~5 phút)
  2. ml: tính features, predict xác suất tăng 5 ngày             (~1 phút)
  3. agents: Batch API chấm sentiment toàn bộ tin mới            (~30–60 phút, async)
  4. agents: orchestrator chạy phân tích sâu từng ticker         (song song, ~10 phút)
  5. fusion: trộn signals → Recommendation, ghi DB
  6. backend: bắn SSE "data mới"; frontend tự refresh
  7. cost report: log token + $ của ngày, so với trần ngân sách
```
