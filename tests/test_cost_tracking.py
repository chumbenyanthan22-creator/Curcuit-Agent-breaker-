from datetime import datetime, timezone

from aggregate_spending_view import AggregateSpendingView
from cost_calculator import CostCalculator


class Query:
    def __init__(self, rows):
        self.rows = rows
    def select(self, *_): return self
    def eq(self, *_): return self
    def gte(self, *_): return self
    def lte(self, *_): return self
    def limit(self, *_): return self
    def execute(self): return {"data": self.rows}


class Client:
    def __init__(self, rows): self.rows, self.calls = rows, 0
    def table(self, _): self.calls += 1; return Query(self.rows)


def test_estimate_cost_uses_configured_rate_per_1k_tokens():
    calc = CostCalculator({"gpt-4": 0.03})
    assert calc.estimate_tokens(4000) == 1000
    assert calc.estimate_cost(4000, "gpt-4") == 0.03


def test_aggregate_cost_sums_session_rows():
    client = Client([{"cost_incurred": "0.02"}, {"cost_incurred": 0.005}])
    calc = CostCalculator({"gpt-4": 0.03}, client)
    total = calc.aggregate_cost("s1", datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 1, 2, tzinfo=timezone.utc))
    assert total == 0.025


def test_daily_spend_is_cached():
    client = Client([
        {"session_id": "s1", "agent_id": "a1", "cost_incurred": "0.02", "executed_at": "2026-01-01T10:00:00Z"},
        {"session_id": "s1", "agent_id": "a1", "cost_incurred": "0.01", "executed_at": "2026-01-01T11:00:00Z"},
    ])
    view = AggregateSpendingView(client, cache_ttl_seconds=300)
    assert view.daily_spend() == [{"day": "2026-01-01", "agent_id": "a1", "total_usd": 0.03}]
    view.daily_spend()
    assert client.calls == 1
