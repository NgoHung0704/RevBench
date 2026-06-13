"""A/B two models on the same news sample (docs/AGENTS.md, docs/DECISIONS.md D3).

Scores an identical sample with the sentiment model and the reasoning model,
side by side, persisting nothing. Answers "is V4-Pro worth 3x the cost for
sentiment?" with data instead of a guess.

Usage:
    python -m agents.compare --limit 10
"""

import argparse

from data_pipeline.store import DEFAULT_DB_PATH

from .config import AgentSettings
from .llm import CallUsage, LLMClient
from .prompts.sentiment import SENTIMENT_SYSTEM
from .roster.sentiment import build_user_message
from .schemas import SentimentOutput
from .store import AgentStore


def _score_all(
    client: LLMClient, model: str, sample, max_tokens: int
) -> list[SentimentOutput | None]:
    out: list[SentimentOutput | None] = []
    for row in sample.itertuples():
        try:
            out.append(
                client.complete_json(
                    model=model,
                    system=SENTIMENT_SYSTEM,
                    user=build_user_message(row.ticker, row.title, row.summary),
                    schema=SentimentOutput,
                    max_tokens=max_tokens,
                )
            )
        except Exception as exc:  # comparison must survive one bad row
            print(f"  ! {model} failed on {row.ticker}: {exc}")
            out.append(None)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--max-tokens", type=int, default=300)
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    args = parser.parse_args(argv)

    settings = AgentSettings()
    cost: dict[str, float] = {}

    def tracker(name):
        def _on(u: CallUsage):
            cost[name] = cost.get(name, 0.0) + u.cost_usd
        return _on

    with AgentStore(args.db) as store:
        sample = store.recent_news(args.limit)
        if sample.empty:
            print("No news in DB — run: python -m data_pipeline.jobs")
            return 1

        flash, pro = settings.sentiment_model, settings.reasoning_model
        flash_out = _score_all(
            LLMClient(settings=settings, on_usage=tracker(flash)), flash, sample, args.max_tokens
        )
        pro_out = _score_all(
            LLMClient(settings=settings, on_usage=tracker(pro)), pro, sample, args.max_tokens
        )

    def cell(o: SentimentOutput | None) -> str:
        return f"{o.score:+.2f}/{o.confidence:.2f} {o.event_type}" if o else "FAIL"

    print(f"\n{'ticker':>6}  {flash:>20}  {pro:>20}  headline")
    abs_gap = 0.0
    n = 0
    for row, f, p in zip(sample.itertuples(), flash_out, pro_out, strict=True):
        print(f"{row.ticker:>6}  {cell(f):>20}  {cell(p):>20}  {row.title[:60]}")
        if f and p:
            abs_gap += abs(f.score - p.score)
            n += 1

    print(f"\nmean |score gap| = {abs_gap / n:.3f} over {n} items" if n else "\nno comparable rows")
    print(f"cost: {flash} ${cost.get(flash, 0):.4f} | {pro} ${cost.get(pro, 0):.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
