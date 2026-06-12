# RevBench — Thiết kế hệ Agent

> LLM: **DeepSeek V4** qua OpenAI-compatible API (xem [DECISIONS.md](DECISIONS.md) D3, chốt lại 2026-06-12). Vẫn theo tinh thần D4: gọi SDK trực tiếp (`openai` + `base_url`), không framework trung gian. Model ID của từng agent là **config**, không hard-code — nâng cấp/đổi provider từng agent là đổi 1 dòng.

## Triết lý

- **Agent = nhà phân tích, không phải máy tính.** Số liệu (RSI, P/E, returns) do code tính trước và đưa vào prompt. Agent đọc, suy luận, kết nối thông tin — việc LLM thật sự giỏi.
- **Mọi output là structured JSON**: JSON mode + Pydantic validation (retry 1 lần khi parse fail) → lưu DB, backtest được.
- **Reasoning trail được lưu** và hiển thị trên UI — tính giải thích được là điểm bán hàng chính.
- **Chi phí là ràng buộc thiết kế hạng nhất**: trần $/ngày trong code (`AGENT_DAILY_BUDGET_USD=1`), vượt là dừng + alert. Job chạy trong cửa sổ **off-peak 16:30–00:30 UTC (−50%)** — lịch 22:30 Paris có sẵn đã nằm trong cửa sổ.

## Roster

| Agent | Model | Khi chạy | Input | Output (schema) |
|---|---|---|---|---|
| **Sentiment** | `deepseek-v4-flash` | Hằng đêm, mọi bài mới | Từng bài news (DB) | `{ticker, score: -1..1, confidence, event_type, summary_1line}` |
| **News** | `deepseek-v4-pro` | Daily/ticker | Top tin đã chấm điểm từ DB (RSS + GDELT) | `{key_events[], materiality, catalysts[], citations[]}` |
| **Technical** | `deepseek-v4-pro` | Daily/ticker | Bảng chỉ báo do `ml/features` tính | `{regime, sr_levels[], signal: -1..1, rationale}` |
| **Fundamentals** | `deepseek-v4-pro` | Sau mỗi earnings + weekly | Số liệu quý từ DB (EDGAR) | `{valuation_view, growth_view, red_flags[], signal: -1..1}` |
| **AltData** | `deepseek-v4-pro` | Weekly | Trends/Reddit/pageviews series | `{demand_signal, attention_anomaly, signal: -1..1}` |
| **Risk** | `deepseek-v4-pro` | Daily/ticker | Vol, drawdown, lịch earnings, vị thế đề xuất | `{risk_flags[], max_position_pct, stop_suggestion}` |
| **Strategist** | `deepseek-v4-pro` | Daily/ticker, chạy cuối | Toàn bộ signals + fusion output | `{action, confidence, horizon_days, thesis_for_user, counterarguments[]}` |

**Orchestrator** (code thuần, không phải LLM): chạy DAG trên — fan-out song song News/Technical/Fundamentals/AltData → Risk → Strategist; gom kết quả, ghi DB, track chi phí.

**Lưu ý so với thiết kế Claude cũ:** không còn server-side web search — News Agent làm việc hoàn toàn trên kho tin nội bộ (Phase 1 đã lo việc thu thập). Đây là trade-off đã chấp nhận ở D3.

## Mẫu kỹ thuật chính

```python
# agents/llm.py — client dùng chung (phác thảo)
from openai import OpenAI

client = OpenAI(
    base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    api_key=os.environ["DEEPSEEK_API_KEY"],
)

# agents/roster/sentiment.py — phác thảo
response = client.chat.completions.create(
    model="deepseek-v4-flash",
    max_tokens=512,
    response_format={"type": "json_object"},  # JSON mode
    messages=[
        # system prompt ĐÓNG BĂNG (không timestamp) → prefix cache hit ~99% rẻ hơn
        {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
        {"role": "user", "content": article_text},
    ],
)
result = SentimentOutput.model_validate_json(response.choices[0].message.content)
usage = response.usage  # prompt_tokens (+ cached), completion_tokens → cost guard
```

## Kiểm soát chi phí (bắt buộc, không phải tùy chọn)

1. **System prompt đóng băng** — không nhúng ngày giờ/ID (vỡ prefix cache). Ngữ cảnh động đi vào user message.
2. **Chạy trong cửa sổ off-peak** (16:30–00:30 UTC, −50%) — lịch hiện tại 22:30 Paris đã thỏa.
3. **Cost guard** trong orchestrator: đọc `response.usage` mỗi call (kể cả cached tokens giá riêng), cộng dồn ngày vào DB, vượt `AGENT_DAILY_BUDGET_USD` → dừng + log.
4. **JSON parse fail → retry đúng 1 lần** rồi bỏ qua record đó (log lại) — không retry vô hạn.
5. Khi dev: chạy 2–3 ticker thay vì cả universe.

## Đánh giá agent (Phase 4.5)

- Mọi `signal: -1..1` của agent lưu lịch sử → tính **Information Coefficient** (tương quan signal với forward return) như feature ML thường.
- Ablation: fusion có/không từng agent → bảng "agent nào đáng tiền".
- Sentiment Agent: đánh giá riêng bằng tập nhãn tay ~200 bài (precision/recall theo event_type).
- (Mở rộng nếu cần) So `deepseek-v4-pro` vs model frontier trên 1 mẫu nhỏ — trả lời "trả thêm tiền có đáng không" bằng số liệu.
