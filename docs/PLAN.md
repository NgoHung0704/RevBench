# RevBench — Kế hoạch dự án tổng thể (Master Plan)

> Tài liệu này là "nguồn sự thật" về lộ trình. Mỗi phase có mục tiêu, deliverables, và tiêu chí hoàn thành (Definition of Done). Các lựa chọn công nghệ còn mở được đánh dấu `[D#]` và ghi chi tiết trong [DECISIONS.md](DECISIONS.md).

## Nguyên tắc xuyên suốt

1. **Trung thực về độ khó.** Thị trường gần như hiệu quả (Efficient Market Hypothesis). Mục tiêu thực tế: *directional accuracy* > 52–55% sau chi phí giao dịch, hoặc Sharpe ratio tốt hơn buy-and-hold trên backtest nghiêm túc — đã là kết quả rất tốt. Mọi con số phải đến từ **walk-forward backtest**, không bao giờ từ in-sample.
2. **Baseline trước, fancy sau.** Luôn so với baseline ngu nhất (naive: "mai giá = hôm nay", buy-and-hold). Model/agent nào không thắng baseline thì không được vào sản phẩm.
3. **Tách tín hiệu khỏi giao diện.** Pipeline dữ liệu → model/agent → signal store → API → UI. Mỗi tầng test được độc lập.
4. **Chi phí có kiểm soát.** LLM agent chạy theo lịch (batch), không chạy mỗi request người dùng. Prompt caching + Batch API (giảm 50%) cho khối lượng lớn.
5. **Không phải lời khuyên đầu tư.** Disclaimer ở mọi bề mặt người dùng.

---

## Tổng quan lộ trình

```
Phase 0  Nền tảng & quyết định        ──┐
Phase 1  Data foundation (giá + news)   │  "Làm cho dữ liệu chảy"
Phase 2  Baseline ML + Backtesting    ──┘
Phase 3  Agent system MVP             ──┐
Phase 4  Signal fusion + khuyến nghị    │  "Làm cho hệ thống thông minh"
Phase 5  Alt-data agents              ──┘
Phase 6  Backend API                  ──┐
Phase 7  Frontend web app               │  "Làm cho dùng được & đẹp"
Phase 8  Đánh giá, hoàn thiện, báo cáo──┘
```

Ước lượng tổng: ~12–16 tuần nếu làm part-time (dự án trường), có thể nén nếu làm full-time. Các phase 3–5 và 6–7 có thể chạy song song một phần.

---

## Phase 0 — Nền tảng & quyết định (1–2 tuần)

**Mục tiêu:** chốt các quyết định kiến trúc, dựng môi trường dev, học nền tảng tài chính.

| # | Việc | Ghi chú |
|---|---|---|
| 0.1 | Chốt các quyết định mở `[D1–D12]` | Xem [DECISIONS.md](DECISIONS.md) — **cần thảo luận với bạn** |
| 0.2 | Chốt universe cổ phiếu (~15 mã blue-chip có trên Revolut) | Đề xuất: AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, JPM, V, MA, KO, PG, JNJ, XOM, DIS |
| 0.3 | Setup repo: Python 3.11+, `uv`/`pip`, pre-commit, ruff, pytest; cấu trúc package | |
| 0.4 | Đăng ký API keys: data provider `[D1]`, Anthropic, Reddit, … | Lưu vào `.env` (không commit) |
| 0.5 | Học finance primer — phần "bắt buộc trước Phase 2" | [FINANCE_PRIMER.md](FINANCE_PRIMER.md) |

**Done khi:** mọi `[D#]` ưu tiên cao đã chốt; `pytest` chạy xanh trên skeleton; tải được 1 năm giá AAPL bằng script demo.

---

## Phase 1 — Data foundation (2–3 tuần)

**Mục tiêu:** dữ liệu giá + tin tức + fundamentals chảy tự động vào storage, sạch và có kiểm tra chất lượng.

| # | Việc | Ghi chú |
|---|---|---|
| 1.1 | Ingestion giá OHLCV daily (+ intraday nếu provider cho phép) cho toàn bộ universe | Provider theo `[D1]`; lưu kèm corporate actions (split, dividend) — dùng **adjusted prices** |
| 1.2 | Ingestion tin tức: RSS các nguồn tài chính + GDELT/NewsAPI `[D7]` | Dedup, gắn ticker (entity linking đơn giản bằng từ khóa trước) |
| 1.3 | Ingestion fundamentals: báo cáo quý (revenue, EPS, margins), lịch earnings | yfinance / SEC EDGAR (miễn phí, chính chủ) |
| 1.4 | Storage layer `[D2]` + schema: `prices`, `news`, `fundamentals`, `signals` | Thiết kế để backtest không bị lookahead (mọi bản ghi có `available_at` timestamp) |
| 1.5 | Scheduler `[D6]`: job daily sau giờ đóng cửa US (22h CET) | Retry + alert khi fail |
| 1.6 | Data quality checks: missing days, outliers, split chưa adjust | Báo cáo tự động |

**Done khi:** chạy 1 lệnh → toàn bộ universe có ≥ 5 năm giá sạch + news 30 ngày gần nhất; job hằng ngày tự chạy.

**⚠️ Bẫy phải tránh:** lookahead bias (dùng dữ liệu chưa tồn tại tại thời điểm dự đoán), survivorship bias (universe cố định hiện tại — chấp nhận & ghi rõ giới hạn này trong báo cáo).

---

## Phase 2 — Baseline ML + Backtesting engine (2–3 tuần)

**Mục tiêu:** có khung đánh giá nghiêm túc TRƯỚC khi xây gì thông minh. Đây là phase quan trọng nhất về mặt khoa học.

| # | Việc | Ghi chú |
|---|---|---|
| 2.1 | Backtest engine `[D11]`: walk-forward (train trên quá khứ, test trên tương lai, trượt cửa sổ) | Mô phỏng phí giao dịch (~0.1%/lượt) + slippage |
| 2.2 | Metrics chuẩn: directional accuracy, Sharpe, Sortino, max drawdown, hit rate, turnover — so với buy-and-hold | Một module `metrics.py` dùng chung mãi mãi |
| 2.3 | Baselines: naive (random walk), momentum đơn giản (12-1), ARIMA | Để biết "sàn" là gì |
| 2.4 | Feature engineering v1: returns, volatility, RSI, MACD, Bollinger, volume features, calendar features | Tất cả lag đúng (chỉ dùng dữ liệu ≤ t để dự đoán t+1) |
| 2.5 | Model ML v1: **LightGBM/XGBoost** dự đoán xác suất giá tăng horizon 1–5 ngày | Tabular gradient boosting thắng deep learning trong đa số bài toán tài chính tần suất thấp — bắt đầu từ đây, không phải LSTM |
| 2.6 | (Stretch) Model v2: LSTM / Temporal Fusion Transformer để so sánh | Chỉ làm nếu v1 đã chạy ổn |

**Done khi:** lệnh `python -m ml.backtest --model lgbm --universe all` in ra bảng metrics so với baselines, kết quả tái lập được (seed cố định).

---

## Phase 3 — Agent system MVP (2–3 tuần)

**Mục tiêu:** hệ agent dùng Claude API đọc tin, chấm sentiment, phân tích kỹ thuật & cơ bản, xuất "agent signal" có cấu trúc cho từng ticker. Chi tiết thiết kế: [AGENTS.md](AGENTS.md).

| # | Việc | Ghi chú |
|---|---|---|
| 3.1 | Khung agent: Anthropic Python SDK, tool use, structured outputs (`output_config.format` + Pydantic) `[D4]` | Model: `claude-opus-4-8` cho orchestrator/analyst; batch + model rẻ hơn cho việc khối lượng lớn `[D3]` |
| 3.2 | **News Agent**: tổng hợp tin theo ticker (từ DB Phase 1 + server-side web search khi cần), tóm tắt sự kiện trọng yếu | Có citation về nguồn |
| 3.3 | **Sentiment Agent**: chấm điểm sentiment từng bài (−1..+1, confidence) qua **Batch API** (rẻ 50%) | Đầu ra structured JSON, lưu vào `signals` |
| 3.4 | **Technical Agent**: nhận chỉ báo từ `ml/features`, diễn giải trạng thái kỹ thuật | Agent diễn giải, KHÔNG tự tính số — số do code tính |
| 3.5 | **Fundamentals Agent**: đọc earnings/filings gần nhất, đánh giá định giá tương đối | SEC EDGAR full-text |
| 3.6 | **Orchestrator**: chạy theo lịch daily, fan-out agents song song, gom kết quả | Prompt caching cho system prompt + tool list |
| 3.7 | Logging & cost tracking: token usage, $ per run, lưu reasoning trail | Trần ngân sách/ngày, dừng khi vượt |

**Done khi:** `python -m agents.run --ticker AAPL` xuất 1 báo cáo JSON: signal từng agent + tóm tắt + chi phí; chạy daily cho cả universe < ngân sách định trước.

---

## Phase 4 — Signal fusion + Recommendation engine (2 tuần)

**Mục tiêu:** trộn tín hiệu ML (Phase 2) + tín hiệu agents (Phase 3) thành khuyến nghị cuối: Buy/Hold/Sell + confidence + lý do + risk.

| # | Việc | Ghi chú |
|---|---|---|
| 4.1 | Schema `Recommendation`: action, confidence, horizon, expected range, rationale, risk flags | |
| 4.2 | Fusion v1: weighted ensemble (trọng số học từ backtest) hoặc stacking — ML signal là xương sống, agent signals là feature bổ sung | **Backtest được** vì agent signals cũng lưu lịch sử |
| 4.3 | **Risk Agent**: kiểm tra concentration, volatility regime, earnings sắp tới, đề xuất position sizing (fractional Kelly / vol targeting) | |
| 4.4 | **Strategist Agent**: viết phần giải thích cho người dùng cuối — ngắn gọn, dễ hiểu, trung thực về độ bất định | |
| 4.5 | Backtest lại toàn pipeline fusion so với ML-only và baselines | Câu hỏi nghiên cứu trung tâm của đồ án: *agents có thêm alpha không?* |

**Done khi:** mỗi ticker mỗi ngày có 1 `Recommendation` trong DB, kèm bảng backtest chứng minh (hoặc phủ nhận trung thực) giá trị của agent signals.

---

## Phase 5 — Alternative data agents (2 tuần, có thể cắt)

**Mục tiêu:** thêm nguồn dữ liệu "kiểu Grok/satellite" trong giới hạn ngân sách sinh viên. Thực tế: ảnh vệ tinh thương mại & X API ngoài tầm ngân sách → dùng **proxy miễn phí** có giá trị nghiên cứu tương đương. Chi tiết: [DATA_SOURCES.md](DATA_SOURCES.md) `[D7][D8]`.

| # | Việc | Nguồn |
|---|---|---|
| 5.1 | Search interest agent | Google Trends (pytrends), Wikipedia pageviews |
| 5.2 | Social agent | Reddit API (r/stocks, r/wallstreetbets), StockTwits public API |
| 5.3 | Consumer traction agent | App store rankings (Sensor Tower public data / app charts), web traffic ước lượng |
| 5.4 | Đánh giá: từng nguồn alt-data có predictive power không (information coefficient) | Giữ nguồn có IC > 0 ổn định, bỏ phần còn lại |

**Done khi:** ≥ 2 nguồn alt-data vào pipeline với đánh giá IC định lượng.

---

## Phase 6 — Backend API (1–2 tuần)

**Mục tiêu:** FastAPI phục vụ frontend; KHÔNG chạy agent theo request — chỉ đọc kết quả đã tính sẵn.

| # | Việc |
|---|---|
| 6.1 | FastAPI + endpoints: `/tickers`, `/tickers/{t}/prices`, `/tickers/{t}/recommendation`, `/tickers/{t}/agents` (reasoning trail), `/portfolio/suggest` |
| 6.2 | Auth đơn giản (API key / session) — đủ cho demo |
| 6.3 | WebSocket/SSE đẩy cập nhật khi job daily xong |
| 6.4 | OpenAPI docs tự sinh; tests cho mọi endpoint |

---

## Phase 7 — Frontend web app (2–3 tuần)

**Mục tiêu:** giao diện đẹp, dễ dùng `[D5]`.

| # | Việc |
|---|---|
| 7.1 | Stack: Next.js + TypeScript + Tailwind + shadcn/ui; charts bằng TradingView **lightweight-charts** |
| 7.2 | Trang Dashboard: watchlist, heatmap khuyến nghị, top movers |
| 7.3 | Trang Ticker: candlestick + overlay tín hiệu, recommendation card, tab "Agent insights" hiển thị reasoning từng agent (điểm khác biệt của sản phẩm) |
| 7.4 | Trang Strategy: gợi ý phân bổ danh mục + risk metrics |
| 7.5 | Dark mode, responsive, disclaimer banner |

**Mẹo tiến độ:** nếu cần demo sớm, dựng **Streamlit** 1–2 ngày ở cuối Phase 4 làm UI tạm, rồi thay bằng Next.js ở phase này.

---

## Phase 8 — Đánh giá, hoàn thiện, báo cáo (1–2 tuần)

| # | Việc |
|---|---|
| 8.1 | Paper-trading 2–4 tuần: ghi khuyến nghị ra trước, đối chiếu kết quả thật |
| 8.2 | Ablation study: ML-only vs ML+agents vs agents-only — bảng số liệu cho báo cáo |
| 8.3 | Hardening: error handling, rate limits, cost guard |
| 8.4 | Deployment `[D10]`: Docker Compose (db + api + frontend + scheduler) |
| 8.5 | Báo cáo đồ án + demo video |

---

## Rủi ro chính & đối sách

| Rủi ro | Đối sách |
|---|---|
| Model không thắng baseline (rất có thể!) | Đây vẫn là kết quả khoa học hợp lệ — báo cáo trung thực; sản phẩm vẫn có giá trị ở phần tổng hợp thông tin & giải thích |
| Chi phí LLM vượt ngân sách | Batch API, prompt caching, chạy daily thay vì realtime, trần ngân sách cứng trong code |
| Data provider miễn phí chết/đổi ToS (yfinance hay bị) | Abstraction layer `PriceProvider` — đổi nguồn không đổi code phía trên |
| Lookahead bias làm kết quả ảo | `available_at` timestamp trên mọi bản ghi + review checklist trong FINANCE_PRIMER |
| Ôm đồm (satellite, realtime, options…) | Phase 5 là phần cắt được đầu tiên; scope khóa theo PLAN này |
