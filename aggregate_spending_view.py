from __future__ import annotations

from datetime import datetime, timedelta, timezone
import time
from typing import Any


class AggregateSpendingView:
    """Aggregate tool costs by agent/session and UTC day with a short TTL cache."""

    def __init__(self, supabase_client: Any, cache_ttl_seconds: int = 300) -> None:
        self.client = supabase_client
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}

    def daily_spend(self, start_time: datetime | str | None = None, end_time: datetime | str | None = None) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        start = start_time or (now - timedelta(days=30))
        end = end_time or now
        key = f"{_iso(start)[:10]}|{_iso(end)[:10]}"
        cached = self._cache.get(key)
        if cached and time.monotonic() - cached[0] < self.cache_ttl_seconds:
            return cached[1]
        response = (self.client.table("tool_execution_logs")
                    .select("session_id,agent_id,cost_incurred,executed_at")
                    .gte("executed_at", _iso(start))
                    .lte("executed_at", _iso(end))
                    .limit(10000)
                    .execute())
        totals: dict[tuple[str, str], float] = {}
        for row in response.get("data") or []:
            day = str(row.get("executed_at", ""))[:10]
            agent = str(row.get("agent_id") or row.get("session_id") or "unknown")
            totals[(day, agent)] = totals.get((day, agent), 0.0) + float(row.get("cost_incurred") or 0)
        result = [{"day": day, "agent_id": agent, "total_usd": round(total, 8)} for (day, agent), total in sorted(totals.items())]
        self._cache[key] = (time.monotonic(), result)
        return result

    def invalidate(self) -> None:
        self._cache.clear()


def _iso(value: datetime | str) -> str:
    return value.isoformat() if isinstance(value, datetime) else value
