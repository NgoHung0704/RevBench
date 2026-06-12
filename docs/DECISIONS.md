# RevBench — Sổ quyết định (Decision Log)

> Mỗi mục là một lựa chọn còn mở hoặc đã chốt. Format: bối cảnh → các phương án → đề xuất của Claude → **trạng thái**. Khi bạn chốt, đổi trạng thái thành ✅ và ghi ngày. Các mục 🔴 cần chốt trước khi bắt đầu phase tương ứng.

| ID | Chủ đề | Cần trước | Trạng thái |
|---|---|---|---|
| D1 | Nguồn dữ liệu giá | Phase 1 | ✅ Chốt 2026-06-12 |
| D2 | Storage layer | Phase 1 | ✅ Chốt 2026-06-12 |
| D3 | LLM & chiến lược chi phí | Phase 3 | ✅ Chốt 2026-06-12 |
| D4 | Agent framework | Phase 3 | ✅ Chốt 2026-06-12 |
| D5 | Frontend stack | Phase 7 | 🟢 Mở (chưa gấp) |
| D6 | Job scheduling | Phase 1 | ✅ Chốt 2026-06-12 |
| D7 | Nguồn social/news data | Phase 1/5 | ✅ Chốt 2026-06-12 |
| D8 | "Satellite data" — phạm vi thực tế | Phase 5 | ✅ Chốt 2026-06-12 |
| D9 | Universe cổ phiếu & horizon dự đoán | Phase 0 | ✅ Chốt 2026-06-12 |
| D10 | Deployment | Phase 8 | 🟢 Mở (chưa gấp) |
| D11 | Backtesting library | Phase 2 | ✅ Chốt 2026-06-12 |
| D12 | Ngôn ngữ tài liệu/báo cáo | Phase 0 | 🟢 Mở |

---

## D1 — Nguồn dữ liệu giá (market data provider) 🔴

**Bối cảnh:** cần OHLCV daily ≥ 5 năm cho ~15 mã US, cập nhật hằng ngày. Ngân sách: ~0 €.

| Phương án | Ưu | Nhược |
|---|---|---|
| **yfinance** (scrape Yahoo) | Miễn phí, không key, lịch sử dài, có fundamentals | Không chính thức, hay vỡ khi Yahoo đổi; không dùng được production thật |
| **Finnhub** free tier | API chính thức, 60 calls/phút, có news + fundamentals | Lịch sử candle daily bị giới hạn ở free tier |
| **Alpha Vantage** free | Chính thức, daily adjusted tốt | 25 requests/ngày (rất chật) |
| **Polygon.io** free | Chất lượng cao | 5 calls/phút, delayed, lịch sử 2 năm |
| **Stooq / Tiingo** | Tiingo free khá rộng rãi (lịch sử dài) | Tiingo cần key, giới hạn 50 symbols/giờ |

**Đề xuất:** **yfinance làm nguồn chính cho dev/backtest + Tiingo hoặc Finnhub làm nguồn thứ hai để cross-check**, tất cả sau một interface `PriceProvider` để đổi nguồn không đau. Chấp nhận yfinance vỡ thỉnh thoảng vì đây là đồ án nghiên cứu.

**Trạng thái:** ✅ Chốt 2026-06-12 — yfinance nguồn chính (dev/backtest), Tiingo dự phòng, tất cả sau interface `PriceProvider`.

---

## D2 — Storage layer 🔴

**Bối cảnh:** dữ liệu ~15 mã × 5 năm daily là *nhỏ* (vài MB). News + signals lớn hơn chút. Web app cần đọc nhanh.

| Phương án | Ưu | Nhược |
|---|---|---|
| **DuckDB + Parquet** | Zero-ops, nhanh khủng khiếp cho analytics, hoàn hảo cho backtest, file-based dễ backup | Không thiết kế cho nhiều writer đồng thời (web app ghi) |
| **PostgreSQL (+ TimescaleDB)** | Chuẩn production, FastAPI tích hợp tốt, đa user | Phải vận hành (Docker), overkill cho data nhỏ |
| **SQLite** | Đơn giản nhất | Analytics chậm hơn DuckDB, concurrency kém |

**Đề xuất:** **lai** — DuckDB/Parquet cho research & backtest (ml/), PostgreSQL (Docker) cho serving (signals, recommendations, users) từ Phase 6. Trước Phase 6 chỉ cần DuckDB. → Bắt đầu bằng DuckDB, thêm Postgres sau, không phải chọn ngay cả hai.

**Trạng thái:** ✅ Chốt 2026-06-12 — DuckDB/Parquet cho research & backtest; thêm PostgreSQL cho serving từ Phase 6.

---

## D3 — LLM & chiến lược chi phí 🟡

**Bối cảnh:** agent system là trái tim dự án. Đã tra cứu Claude API (06/2026):

| Model | Input $/1M tok | Output $/1M tok | Vai trò đề xuất |
|---|---|---|---|
| `claude-opus-4-8` | $5 | $25 | Orchestrator, Fundamentals, Strategist, Risk — việc cần suy luận sâu |
| `claude-haiku-4-5` | $1 | $5 | Sentiment scoring khối lượng lớn (hàng trăm bài/ngày) |

Đòn bẩy chi phí có sẵn trên API:
- **Batch API**: −50% mọi token, hoàn hảo cho sentiment hằng đêm (không cần realtime).
- **Prompt caching**: system prompt + tool list dùng chung → đọc cache ~0.1× giá.
- **Server-side web search tool** (`web_search_20260209`): News Agent tìm web không cần tự dựng crawler.
- **Structured outputs**: bắt JSON đúng schema Pydantic, không phải parse text.

Ước lượng thô: 15 ticker × (1 orchestrator run ~30K tok in / 5K out trên Opus + 50 bài sentiment trên Haiku batch) ≈ **$3–6/ngày** chạy daily. Chấp nhận được nếu chỉ chạy ngày giao dịch (~21 ngày/tháng → $60–130/tháng; có thể giảm tiếp bằng cách chạy 3 lần/tuần khi dev).

**Phương án khác đã cân nhắc:** OpenAI/Gemini (khả thi tương đương, nhưng tôi viết & debug hệ Claude tốt nhất, và skill/tooling sẵn có trong repo này hướng Claude); local LLM qua Ollama (miễn phí nhưng chất lượng suy luận tài chính kém hơn rõ, thêm độ phức tạp vận hành).

**Đề xuất:** Claude API; Opus 4.8 cho reasoning, Haiku 4.5 + Batch cho bulk sentiment; ngân sách trần cứng trong code (ví dụ $5/ngày).

**Trạng thái:** ✅ Chốt 2026-06-12 — Claude API: Opus 4.8 (reasoning), Haiku 4.5 + Batch API (bulk sentiment); trần cứng `AGENT_DAILY_BUDGET_USD=5`.

---

## D4 — Agent framework 🟡

| Phương án | Ưu | Nhược |
|---|---|---|
| **Anthropic SDK trực tiếp** (tool runner + structured outputs) | Không thêm dependency, kiểm soát hoàn toàn, dễ debug, prompt caching/batch dùng thẳng | Tự viết orchestration (nhưng orchestration của ta đơn giản: fan-out → gom) |
| LangGraph / LangChain | Nhiều pattern sẵn | Trừu tượng dày, khó debug, API đổi liên tục, che mất chi tiết caching |
| Claude Agent SDK / Managed Agents | Anthropic lo vòng lặp agent | Overkill — agent của ta chạy batch theo lịch, không cần session container |

**Đề xuất:** **Anthropic Python SDK trực tiếp.** Orchestration của RevBench là DAG đơn giản chạy theo lịch — một framework đồ sộ chỉ thêm rủi ro. Nếu sau này cần hội thoại đa lượt phức tạp giữa agents thì xét lại.

**Trạng thái:** ✅ Chốt 2026-06-12 — Anthropic Python SDK trực tiếp, không framework trung gian.

---

## D5 — Frontend stack 🟢

| Phương án | Ưu | Nhược |
|---|---|---|
| **Next.js + Tailwind + shadcn/ui + lightweight-charts** | Đẹp, chuẩn ngành, SSR, hệ sinh thái chart tài chính tốt | Học phí nếu chưa quen React |
| Vite + React SPA | Nhẹ hơn Next | Tự lo routing/SSR |
| Streamlit | Dựng trong 1 ngày | Trần thẩm mỹ thấp — không đạt mục tiêu "giao diện đẹp" |

**Đề xuất:** Next.js cho sản phẩm cuối; Streamlit chỉ làm UI tạm nội bộ nếu cần demo sớm. **Câu hỏi cho bạn:** bạn đã quen React/TypeScript chưa? Nếu chưa, ta cân nhắc Vite+React (đơn giản hơn Next) — vẫn đẹp được.

**Trạng thái:** 🟢 Chốt trước Phase 7 là được.

---

## D6 — Job scheduling 🟡

| Phương án | Ưu | Nhược |
|---|---|---|
| **APScheduler trong 1 process Python** | Đơn giản nhất, đủ cho 1 máy | Không có UI, không distributed |
| Prefect / Dagster | Observability đẹp, retry xịn | Thêm hạ tầng phải nuôi |
| cron / Task Scheduler (Windows) | Zero code | Khó quản lý dependency giữa jobs |

**Đề xuất:** APScheduler (kèm logging tử tế) cho toàn bộ vòng đời đồ án; Prefect chỉ khi pipeline phình to thật sự.

**Trạng thái:** ✅ Chốt 2026-06-12 — APScheduler trong 1 process.

---

## D7 — Nguồn social/news data 🟡

**Thực tế phũ phàng:** X (Twitter) API tier đọc được data giá $100+/tháng — kiểu "Grok đọc Twitter" **ngoài ngân sách**. Thay thế khả thi:

| Nguồn | Phí | Giá trị |
|---|---|---|
| **Reddit API** (r/stocks, r/wallstreetbets, r/investing) | Free tier đủ dùng | Sentiment bán lẻ — chính là nơi meme-stock sentiment sống |
| **StockTwits API** | Free public | Sentiment gắn ticker sẵn ($AAPL tags) |
| **GDELT** | Free | Tin tức toàn cầu, độ phủ khổng lồ |
| **RSS** (Reuters, CNBC, Yahoo Finance, SeekingAlpha) | Free | Tin chính thống |
| NewsAPI.org | Free tier 100 req/ngày, delay 24h | Tiện nhưng giới hạn |

**Đề xuất:** RSS + GDELT (tin chính thống) + Reddit + StockTwits (sentiment bán lẻ). Bỏ X/Twitter, ghi rõ trong báo cáo là giới hạn ngân sách.

**Trạng thái:** ✅ Chốt 2026-06-12 — RSS + GDELT + Reddit + StockTwits; bỏ X/Twitter (ngân sách — ghi limitation vào báo cáo).

---

## D8 — "Satellite data" — phạm vi thực tế 🟡

**Bối cảnh:** ý tưởng gốc — ảnh vệ tinh đếm xe ở bãi đỗ Walmart, Google Maps foot traffic. Thực tế: ảnh vệ tinh thương mại (Orbital Insight, RS Metrics) giá hàng nghìn $/tháng; Google Maps "Popular Times" không có API chính thức (scrape vi phạm ToS).

**Proxy miễn phí có cùng tinh thần "đo hoạt động thực của doanh nghiệp":**

1. **Google Trends** — search interest cho brand/sản phẩm (iPhone, Tesla Model Y…) → proxy nhu cầu tiêu dùng.
2. **Wikipedia pageviews** — attention proxy, có nghiên cứu học thuật chứng minh tương quan với volume.
3. **App store rankings** — proxy traction cho công ty consumer (Meta, Google apps).
4. **Job postings count** (career pages, levels.fyi trends) — proxy tăng trưởng/thu hẹp.
5. (Stretch) **Sentinel-2 ảnh vệ tinh miễn phí của ESA** — phân giải 10m, đủ cho nghiên cứu mức "hoạt động cảng/nhà máy" nếu muốn có yếu tố satellite thật trong báo cáo; nhưng effort lớn, để stretch goal.

**Đề xuất:** 1–3 vào Phase 5; mục 5 chỉ làm nếu dư thời gian và muốn "wow factor" cho báo cáo.

**Trạng thái:** ✅ Chốt 2026-06-12 — Google Trends + Wikipedia pageviews + app charts vào Phase 5; Sentinel-2 là stretch goal.

---

## D9 — Universe & horizon dự đoán 🔴

**Cần bạn chốt 3 điều:**

1. **Universe:** 15 mã đề xuất ở PLAN 0.2 ổn chưa? (tiêu chí: blue-chip, có trên Revolut, thanh khoản cao, đủ đa dạng ngành). Có muốn thêm cổ phiếu châu Âu trên Revolut không? (khuyên: chưa — thêm múi giờ & nguồn data phức tạp).
2. **Horizon:** dự đoán 1 ngày / 5 ngày / 20 ngày? **Đề xuất: 5 ngày (1 tuần giao dịch)** — đủ ngắn để backtest nhiều mẫu, đủ dài để tín hiệu news/fundamentals kịp "ngấm" và phí giao dịch không nuốt hết alpha.
3. **Bài toán:** phân loại hướng (lên/xuống — dễ đánh giá, đề xuất) hay hồi quy mức giá (khó hơn nhiều)?

**Trạng thái:** ✅ Chốt 2026-06-12 — universe 15 mã US như đề xuất (chưa thêm cổ phiếu châu Âu); horizon **5 ngày giao dịch**; bài toán **phân loại hướng** (lên/xuống).

---

## D10 — Deployment 🟢

Đề xuất khi đến lúc: Docker Compose chạy local/VPS rẻ (Hetzner ~5€/tháng) hoặc free tier (frontend lên Vercel, API lên Railway/Fly.io). Quyết sau Phase 6.

---

## D11 — Backtesting library 🟡

| Phương án | Nhận xét |
|---|---|
| **Tự viết walk-forward harness (pandas/numpy)** | Bài toán của ta là *signal evaluation* theo lịch daily — engine tự viết ~300 dòng, hiểu 100% những gì xảy ra, là nội dung đẹp cho báo cáo đồ án |
| vectorbt | Rất nhanh nhưng API học phí cao, bản free hạn chế |
| backtesting.py | Gọn nhưng thiên về chiến lược kỹ thuật đơn lẻ, khó nhét ML signals đa mã |

**Đề xuất:** tự viết harness + dùng `quantstats` để xuất report metrics đẹp.

**Trạng thái:** ✅ Chốt 2026-06-12 — tự viết walk-forward harness + `quantstats` cho report.

---

## D12 — Ngôn ngữ tài liệu/báo cáo 🟢

Hiện tại: docs tiếng Việt (làm việc với bạn), README + code + comments tiếng Anh. Báo cáo nộp trường (Pháp/Anh?) — bạn cho biết yêu cầu của INSA để tính việc dịch.

**Trạng thái:** 🟢 Chốt lúc nào cũng được.
