# RevBench — Thiết kế hệ Agent

> Xây trên **Anthropic Python SDK trực tiếp** (xem [DECISIONS.md](DECISIONS.md) D4): tool use + structured outputs + prompt caching + Batch API. Không framework trung gian.

## Triết lý

- **Agent = nhà phân tích, không phải máy tính.** Số liệu (RSI, P/E, returns) do code tính trước và đưa vào prompt. Agent đọc, suy luận, kết nối thông tin — việc LLM thật sự giỏi.
- **Mọi output là structured JSON** (Pydantic schema + `output_config.format`) → lưu DB, backtest được, không parse text thủ công.
- **Reasoning trail được lưu** và hiển thị trên UI — tính giải thích được là điểm bán hàng chính của sản phẩm.
- **Chi phí là ràng buộc thiết kế hạng nhất**: trần $/ngày trong code, vượt là dừng và alert.

## Roster

| Agent | Model | Khi chạy | Input | Output (schema) |
|---|---|---|---|---|
| **Sentiment** | Haiku 4.5 qua **Batch API** | Hằng đêm, mọi bài mới | Từng bài news/post | `{ticker, score: -1..1, confidence, event_type, summary_1line}` |
| **News** | Opus 4.8 | Daily/ticker | Top tin đã chấm điểm + server-side `web_search` khi cần đào sâu | `{key_events[], materiality, catalysts[], citations[]}` |
| **Technical** | Opus 4.8 | Daily/ticker | Bảng chỉ báo do `ml/features` tính | `{regime, sr_levels[], signal: -1..1, rationale}` |
| **Fundamentals** | Opus 4.8 | Sau mỗi earnings + weekly | Số liệu quý, trích đoạn filing (EDGAR) | `{valuation_view, growth_view, red_flags[], signal: -1..1}` |
| **AltData** | Opus 4.8 | Weekly | Trends/Reddit/pageviews series | `{demand_signal, attention_anomaly, signal: -1..1}` |
| **Risk** | Opus 4.8 | Daily/ticker | Vol, drawdown, lịch earnings, vị thế đề xuất | `{risk_flags[], max_position_pct, stop_suggestion}` |
| **Strategist** | Opus 4.8 | Daily/ticker, chạy cuối | Toàn bộ signals + fusion output | `{action, confidence, horizon_days, thesis_for_user, counterarguments[]}` |

**Orchestrator** (code thuần, không phải LLM): chạy DAG trên — fan-out song song News/Technical/Fundamentals/AltData → Risk → Strategist; gom kết quả, ghi DB, track chi phí.

## Mẫu kỹ thuật chính

```python
# agents/roster/sentiment.py — phác thảo
from anthropic import Anthropic
from anthropic.types.messages.batch_create_params import Request

# Bulk sentiment qua Batch API (rẻ 50%), structured output ép schema
requests = [
    Request(
        custom_id=f"sent-{article.id}",
        params=MessageCreateParamsNonStreaming(
            model="claude-haiku-4-5",
            max_tokens=512,
            system=[{
                "type": "text",
                "text": SENTIMENT_SYSTEM_PROMPT,        # cố định, không timestamp
                "cache_control": {"type": "ephemeral"},  # prompt caching
            }],
            output_config={"format": SENTIMENT_JSON_SCHEMA},
            messages=[{"role": "user", "content": article.text}],
        ),
    )
    for article in new_articles
]
batch = client.messages.batches.create(requests=requests)
```

```python
# agents/roster/news.py — News Agent với server-side web search
response = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=16000,
    thinking={"type": "adaptive"},
    tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 5}],
    system=[{"type": "text", "text": NEWS_SYSTEM_PROMPT,
             "cache_control": {"type": "ephemeral"}}],
    messages=[{"role": "user", "content": build_news_context(ticker, day)}],
)
```

## Kiểm soát chi phí (bắt buộc, không phải tùy chọn)

1. **System prompt đóng băng** — không nhúng ngày giờ/ID vào system prompt (vỡ prompt cache). Ngữ cảnh động đi vào user message.
2. **Batch API** cho mọi việc không cần kết quả ngay (sentiment, tóm tắt hàng loạt).
3. **Cost guard** trong orchestrator: đếm token từ `response.usage` mỗi call, cộng dồn ngày, vượt trần → dừng + log.
4. **Cache tool list & system theo đúng thứ tự render** `tools → system → messages`; breakpoint ở block system cuối.
5. Khi dev: chạy 2–3 ticker thay vì cả universe.

## Đánh giá agent (Phase 4.5)

- Mọi `signal: -1..1` của agent lưu lịch sử → tính **Information Coefficient** (tương quan signal với forward return) như feature ML thường.
- Ablation: fusion có/không từng agent → bảng "agent nào đáng tiền".
- Sentiment Agent: đánh giá riêng bằng tập nhãn tay ~200 bài (precision/recall theo event_type).
