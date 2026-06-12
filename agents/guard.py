"""Hard daily budget ceiling (CLAUDE.md hard rule #3).

Checked before every LLM call; once the ledger crosses the ceiling, the run
stops — no "just one more article".
"""

from .store import AgentStore


class BudgetExceededError(RuntimeError):
    pass


class CostGuard:
    def __init__(self, store: AgentStore, budget_usd: float):
        self.store = store
        self.budget_usd = budget_usd

    def check(self) -> None:
        spent = self.store.spent_today_usd()
        if spent >= self.budget_usd:
            raise BudgetExceededError(
                f"daily LLM budget exhausted: ${spent:.4f} >= ${self.budget_usd:.2f}"
            )
