from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .slack_alerter import SlackAlerter

from .cost_calculator import CostCalculator


class SupabaseLike(Protocol):
    def table(self, name: str) -> Any: ...


@dataclass(frozen=True)
class PendingWrite:
    table: str
    payload: dict[str, Any]
    error: str
    queued_at: str


class SupabaseLogger:
    """Direct detector-table writer with a local JSONL retry outbox.

    If no client is supplied, the constructor connects using SUPABASE_URL and
    SUPABASE_KEY. DDL is deliberately deployed through Supabase migrations rather
    than executed by an application using a public/anon key.
    """

    REQUIRED_TABLES = ("agent_sessions", "tool_execution_logs", "agent_alerts")
    DEFAULT_WORKSPACE_ID = "11111111-1111-1111-1111-111111111111"

    def __init__(self, client: SupabaseLike | None = None, outbox_path: str | Path = ".agentbreaker-outbox.jsonl", slack_alerter: "SlackAlerter | None" = None, cost_calculator: CostCalculator | None = None) -> None:
        if client is None:
            from dotenv import load_dotenv
            from supabase import create_client

            load_dotenv()
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_KEY")
            if not url or not key:
                raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required")
            client = create_client(url, key)
        self.client = client
        self.outbox_path = Path(outbox_path)
        self.slack_alerter = slack_alerter
        self.cost_calculator = cost_calculator or CostCalculator.from_config_file(supabase_client=client)
        self.last_cost_usd = 0.0
        self.last_output_tokens = 0
        self.missing_tables: list[str] = []
        self._check_tables()

    def _check_tables(self) -> None:
        for table in self.REQUIRED_TABLES:
            try:
                self.client.table(table).select("*").limit(1).execute()
            except Exception:
                self.missing_tables.append(table)

    @property
    def schema_ready(self) -> bool:
        return not self.missing_tables

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _args_hash(args: dict[str, Any]) -> str:
        encoded = json.dumps(args, sort_keys=True, separators=(",", ":"), default=str).encode()
        return hashlib.sha256(encoded).hexdigest()

    def _try_write(self, table: str, payload: dict[str, Any]) -> tuple[bool, str | None]:
        try:
            self.client.table(table).insert(payload).execute()
            return True, None
        except Exception as exc:  # noqa: BLE001 - network/client errors are queued
            return False, str(exc)

    def _write(self, table: str, payload: dict[str, Any]) -> bool:
        success, error = self._try_write(table, payload)
        if not success:
            self._queue(table, payload, error or "Supabase write failed")
        return success

    def _queue(self, table: str, payload: dict[str, Any], error: str | Exception) -> None:
        pending = PendingWrite(table, payload, str(error), self._now())
        self.outbox_path.parent.mkdir(parents=True, exist_ok=True)
        with self.outbox_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(asdict(pending), default=str) + "\n")

    def ensure_session(self, session_id: str, company_id: str | None = None, max_budget_usd: float = 10.0) -> bool:
        payload = {
            "session_id": session_id,
            "company_id": company_id,
            "max_budget_usd": float(max_budget_usd),
            "current_spend_usd": 0.0,
            "is_paused": False,
            "created_at": self._now(),
        }
        try:
            self.client.table("agent_sessions").upsert(payload, on_conflict="session_id").execute()
            return True
        except Exception as exc:  # noqa: BLE001
            self._queue("agent_sessions", payload, exc)
            return False

    def log_tool_call(self, session_id: str, tool_name: str, args: dict[str, Any], output: Any, cost_usd: float | None = None, model_name: str = "gpt-4", agent_id: str | None = None) -> bool:
        output_length = len(str(output))
        self.last_output_tokens = self.cost_calculator.estimate_tokens(output_length)
        self.last_cost_usd = self.cost_calculator.estimate_cost(output_length, model_name)
        payload = {
            "session_id": session_id,
            "tool_name": tool_name,
            "arguments_hash": self._args_hash(args),
            "cost_incurred": self.last_cost_usd,
            "model_name": model_name,
            "output_tokens_estimated": self.last_output_tokens,
            "executed_at": self._now(),
        }
        if agent_id:
            payload["agent_id"] = agent_id
        written = self._write("tool_execution_logs", payload)
        self.increment_session_spend(session_id, self.last_cost_usd)
        return written

    def log_loop_detection(self, session_id: str, loop_info: dict[str, Any], tool_name: str, fingerprint: str) -> bool:
        payload = {
            "session_id": session_id,
            "alert_type": str(loop_info.get("alert_type", "loop_detected")),
            "fingerprint": fingerprint,
            "cycle_length": int(loop_info.get("cycle_length", 1)),
            "created_at": self._now(),
        }
        written = self._write("agent_alerts", payload)
        if self.slack_alerter is not None:
            self.slack_alerter.alert_loop(session_id, {**loop_info, "fingerprint": fingerprint}, tool_name)
        return written

    def log_budget_exceeded(self, session_id: str, tool_name: str, estimated_cost_usd: float, max_budget_usd: float) -> bool:
        """Record a budget block without sending a loop alert to Slack."""
        payload = {
            "session_id": session_id,
            "alert_type": "budget_exceeded",
            "fingerprint": f"budget:{session_id}",
            "cycle_length": 0,
            "created_at": self._now(),
        }
        return self._write("agent_alerts", payload)

    def pause_session(self, session_id: str, reason: str) -> bool:
        return self._update("agent_sessions", {"is_paused": True}, {"session_id": session_id}, reason=reason)

    def resume_session(self, session_id: str) -> bool:
        return self._update("agent_sessions", {"is_paused": False}, {"session_id": session_id})

    def update_session_spend(self, session_id: str, current_spend: float) -> bool:
        return self._update("agent_sessions", {"current_spend_usd": float(current_spend)}, {"session_id": session_id})

    def increment_session_spend(self, session_id: str, delta_usd: float) -> bool:
        try:
            response = (self.client.table("agent_sessions").select("current_spend_usd")
                        .eq("session_id", session_id).limit(1).execute())
            rows = response.get("data") or []
            current = float((rows[0] or {}).get("current_spend_usd") or 0) if rows else 0.0
            return self._update("agent_sessions", {"current_spend_usd": round(current + float(delta_usd), 8)}, {"session_id": session_id})
        except Exception as exc:  # noqa: BLE001
            self._queue("agent_sessions", {"session_id": session_id, "spend_increment_usd": float(delta_usd)}, exc)
            return False

    def _update(self, table: str, values: dict[str, Any], filters: dict[str, Any], **context: Any) -> bool:
        try:
            query = self.client.table(table).update(values)
            for key, value in filters.items():
                query = query.eq(key, value)
            query.execute()
            return True
        except Exception as exc:  # noqa: BLE001
            self._queue(table, {**values, **filters, **context}, exc)
            return False

    def record_decision(self, session_id: str, decision: dict[str, Any] | str, timestamp: str | None = None) -> bool:
        payload = {
            "session_id": session_id,
            "action": str(decision.get("action", "tool_call") if isinstance(decision, dict) else "tool_call"),
            "decision": json.dumps(decision, default=str) if isinstance(decision, dict) else str(decision),
            "timestamp": timestamp or self._now(),
        }
        success, error = self._try_write("audit_events", payload)
        if success:
            return True
        # The project’s original audit_events table uses the dashboard schema.
        # Preserve the decision in that live table when the requested shape differs.
        action = payload["action"]
        blocked = "blocked" in payload["decision"] or "loop" in payload["decision"]
        compatibility_payload = {
            "workspace_id": os.environ.get("AGENTBREAKER_WORKSPACE_ID", self.DEFAULT_WORKSPACE_ID),
            "agent_name": "Live detector",
            "action": action,
            "detail": payload["decision"],
            "outcome": "blocked" if blocked else "allowed",
            "risk_level": "critical" if blocked else "low",
            "metadata": {"session_id": session_id, "source": "langchain_handler"},
            "created_at": payload["timestamp"],
        }
        compatibility_success, compatibility_error = self._try_write("audit_events", compatibility_payload)
        if not compatibility_success:
            self._queue("audit_events", payload, f"{error}; compatibility: {compatibility_error}")
        return compatibility_success
