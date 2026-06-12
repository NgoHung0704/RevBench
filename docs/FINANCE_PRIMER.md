# RevBench — Lộ trình kiến thức tài chính (Finance Primer)

> Dự án này đứng trên 3 chân: AI Engineering, Data Science, **và Finance**. Chân thứ ba yếu thì hai chân kia xây ra thứ vô dụng (hoặc tệ hơn: thứ *trông* có lãi trên backtest sai). File này là lộ trình học + checklist chống bẫy.

## Khối 1 — Bắt buộc trước Phase 2 (backtest)

### 1.1 Efficient Market Hypothesis (EMH) & vì sao bài toán này khó
- Giá đã phản ánh thông tin công khai → alpha từ dữ liệu công khai là *cực mỏng*.
- Hệ quả thiết kế: kỳ vọng directional accuracy 52–55% là mục tiêu *thực tế tốt*; ai hứa 80% là đang ăn lookahead bias.
- Random walk & vì sao "naive forecast" là baseline phải thắng.

### 1.2 Returns — làm việc với returns, không phải giá
- Simple vs log returns; vì sao model dự trên returns chứ không phải price level (non-stationarity).
- Adjusted price (split/dividend) — dùng sai là feature nhiễm rác.
- Phân phối returns: fat tails, volatility clustering → đừng giả định Gaussian.

### 1.3 Bộ tứ bias chết người (checklist review mọi PR backtest)
| Bias | Nghĩa | Phòng chống trong RevBench |
|---|---|---|
| **Lookahead** | Dùng thông tin chưa tồn tại tại t | Cột `available_at`; features chỉ từ dữ liệu ≤ t |
| **Survivorship** | Universe chỉ gồm kẻ sống sót hôm nay | Chấp nhận với blue-chips, *ghi rõ limitation* trong báo cáo |
| **Overfitting / data snooping** | Thử 100 ý tưởng, báo cáo cái đẹp nhất | Walk-forward; tập test cuối chỉ chạm 1 lần; ghi log mọi thí nghiệm |
| **Transaction cost ignorance** | Lãi trên giấy, lỗ ngoài đời | Mô phỏng phí + slippage trong mọi backtest |

### 1.4 Metrics đánh giá
- Sharpe ratio (và vì sao Sharpe > 2 từ dữ liệu daily công khai là đáng nghi ngờ).
- Sortino, max drawdown, hit rate, profit factor, turnover.
- Information Coefficient (IC) — đo chất lượng *signal* tách khỏi chiến lược.

## Khối 2 — Trước Phase 3–4 (agents & fusion)

### 2.1 Phân tích cơ bản (cho Fundamentals Agent)
- Đọc 10-K/10-Q: income statement, balance sheet, cash flow — chỉ cần mức "biết tìm gì ở đâu".
- Chỉ số: P/E, forward P/E, PEG, EV/EBITDA, gross/operating margin, FCF yield.
- Earnings season: expectations game — giá chạy theo *bất ngờ* (surprise vs consensus), không theo số tuyệt đối.

### 2.2 Phân tích kỹ thuật (cho Technical Agent)
- Momentum (hiện tượng có bằng chứng học thuật mạnh nhất), mean reversion.
- RSI, MACD, Bollinger, moving averages, support/resistance, volume profile — hiểu cơ chế, không thờ phụng.
- Volatility regimes (vol thấp/cao thay đổi hành vi mọi signal).

### 2.3 Tin tức & sentiment
- Event study: giá phản ứng tin trong phút-giờ → tin *hôm qua* chủ yếu dự đoán... volatility, không phải hướng. Đặt kỳ vọng đúng cho Sentiment Agent.
- Loại sự kiện trọng yếu: earnings, guidance, M&A, kiện tụng, thay CEO, nâng/hạ rating, sản phẩm mới, macro (Fed, CPI).

### 2.4 Risk & position sizing (cho Risk Agent)
- Volatility targeting, fractional Kelly (và vì sao full Kelly là tự sát).
- Correlation trong danh mục — 15 mã tech ≠ đa dạng hóa.
- Stop loss: tranh cãi học thuật, nhưng UX cần nó.

## Khối 3 — Nâng cao (nếu dư thời gian / cho báo cáo)
- Factor models: CAPM → Fama-French 3/5 factors → momentum factor. Giúp trả lời "alpha của ta có thật không hay chỉ là beta trá hình".
- Market microstructure cơ bản: bid-ask spread, vì sao slippage tồn tại.
- Văn liệu alt-data: Da, Engelberg & Gao (2011) — Google Trends dự đoán; Moat et al. — Wikipedia pageviews; Bollen et al. (2011) — Twitter mood (và các phê bình replication của nó — đọc cả hai phía!).

## Tài liệu gợi ý
- **Advances in Financial Machine Learning** — Marcos López de Prado (kinh thánh về ML tài chính làm đúng; chương về cross-validation cho time series và backtest overfitting là bắt buộc).
- **Quantitative Trading** — Ernest Chan (nhập môn thực dụng).
- Investopedia cho khái niệm lẻ; SSRN cho papers alt-data.

## Quy tắc văn hóa dự án
1. Con số backtest nào không kèm mô tả phương pháp (cửa sổ, phí, universe) = không tồn tại.
2. "Có vẻ hoạt động" không phải kết luận — IC, p-value, hoặc im lặng.
3. Kết quả âm (agents không thêm alpha) vẫn là kết quả đồ án tốt nếu phương pháp sạch.
