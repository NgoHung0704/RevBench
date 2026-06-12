# RevBench — Catalog nguồn dữ liệu

> Đánh giá theo 4 tiêu chí: phí, độ tin cậy, pháp lý (ToS), giá trị dự đoán kỳ vọng. Trạng thái: ✅ dùng, 🟡 cân nhắc, ❌ loại (ghi lý do để khỏi bàn lại).

## 1. Giá & khối lượng (Phase 1)

| Nguồn | Phí | Ghi chú | Trạng thái |
|---|---|---|---|
| yfinance (Yahoo) | Free | Không chính thức, hay vỡ; lịch sử dài, có adjusted close | ✅ nguồn chính dev `[D1]` |
| Tiingo | Free tier | Chính thức, lịch sử dài, 50 symbols/h | 🟡 nguồn dự phòng |
| Finnhub | Free tier | 60 calls/min, kèm news + fundamentals + earnings calendar | 🟡 đa dụng |
| Alpha Vantage | Free | 25 req/ngày — quá chật | ❌ |
| Polygon.io free | Free | Chỉ 2 năm lịch sử, 5 calls/min | ❌ cho nhu cầu này |

## 2. Tin tức (Phase 1, 3)

| Nguồn | Phí | Ghi chú | Trạng thái |
|---|---|---|---|
| RSS feeds (CNBC, Reuters, Yahoo Finance, MarketWatch, SeekingAlpha) | Free | Ổn định, hợp pháp, realtime tốt | ✅ |
| GDELT 2.0 | Free | Độ phủ khổng lồ, query bằng BigQuery/API; nhiễu cao cần lọc | ✅ |
| NewsAPI.org | Free tier | 100 req/ngày, delay 24h ở free | 🟡 phụ |
| Finnhub company news | Free tier | Gắn ticker sẵn — đỡ công entity linking | ✅ nếu dùng Finnhub |
| Bloomberg/Reuters API | $$$$ | | ❌ ngân sách |
| **Claude server-side web search** | ~$10/1K searches + tokens | News Agent tự tìm khi cần đào sâu — không cần crawler | ✅ có kiểm soát `max_uses` |

## 3. Fundamentals (Phase 1, 3)

| Nguồn | Phí | Ghi chú | Trạng thái |
|---|---|---|---|
| SEC EDGAR (API chính chủ) | Free | 10-K/10-Q/8-K full text + XBRL số liệu chuẩn; rate limit 10 req/s | ✅ nguồn vàng |
| yfinance fundamentals | Free | Tiện nhưng số liệu đôi khi lệch | 🟡 tham khảo nhanh |
| Financial Modeling Prep | Free tier hẹp | | 🟡 |

## 4. Social sentiment (Phase 5) `[D7]`

| Nguồn | Phí | Ghi chú | Trạng thái |
|---|---|---|---|
| Reddit API (PRAW) | Free tier | r/stocks, r/wallstreetbets, r/investing; 100 QPM đủ | ✅ |
| StockTwits public API | Free | Message có cashtag + sentiment label người dùng tự gắn | ✅ |
| X (Twitter) API | $100+/tháng cho read | "Grok đọc Twitter" — ngoài ngân sách | ❌ ngân sách (ghi vào báo cáo là limitation) |
| Facebook/Meta data | Không có API công khai phù hợp | | ❌ |

## 5. Alternative data (Phase 5) `[D8]`

| Nguồn | Phí | Proxy cho | Trạng thái |
|---|---|---|---|
| Google Trends (pytrends) | Free | Nhu cầu tiêu dùng theo brand/sản phẩm | ✅ |
| Wikipedia pageviews API | Free | Investor attention (có literature hỗ trợ) | ✅ |
| App store charts | Free (public) | Traction app consumer (META, GOOGL, …) | 🟡 |
| Job postings (career pages) | Free nhưng phải scrape | Tăng trưởng headcount | 🟡 effort cao |
| Google Maps Popular Times | Không có API; scrape vi phạm ToS | Foot traffic | ❌ pháp lý |
| Ảnh vệ tinh thương mại (RS Metrics, Orbital Insight) | $$$$$ | Foot traffic, hàng tồn | ❌ ngân sách |
| ESA Sentinel-2 (miễn phí, 10m/pixel) | Free | Hoạt động cảng/nhà máy quy mô lớn | 🟡 stretch goal "wow factor" |

## Quy tắc chung

1. **Mọi bản ghi lưu kèm `available_at`** (thời điểm ta *có thể* đã biết thông tin) — không phải `published_at` — để backtest point-in-time đúng.
2. **Tôn trọng ToS & rate limit** — User-Agent tử tế với EDGAR, exponential backoff mọi nơi.
3. **Adapter pattern**: mỗi nguồn một class sau interface chung; nguồn chết thì thay adapter.
4. **Raw data không commit vào git** (đã có trong `.gitignore`) — script tải lại được từ đầu là một deliverable.
