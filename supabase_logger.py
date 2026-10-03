from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Protocol


class SupabaseLike(Protocol):
    def table(self, name: str) -> Any: ...


@dataclass(frozen=True)
class PendingWrite:
    table: str
    payload: dict[str, Any]
    error: str
    queued_at: str


class SupabaseLogger:
    """Direct Supabase writer for the existing AgentBreaker pipeline schema.

    Failed writes are appended to a local JSONL outbox so a later worker can retry
    them. No credentials are persisted by this class.
    """

    def __init__(self, client: SupabaseLike, outbox_path: str | Path = ".agentbreaker-outbox.jsonl") -> None:
        self.client = client
        self.outbox_path = Path(outbox_path)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _args_hash(args: dict[str, Any]) -> str:
        encoded = json.dumps(args, sort_keys=True, separators=(",", ":"), default=str).encode()
        return hashlib.sha256(encoded).hexdigest()

    def _write(self, table: str, payload: dict[str, Any]) -> bool:
        try:
            self.client.table(table).insert(payload).execute()
            return True
        except Exception as exc:  # noqa: BLE001 - network/client errors must be queued
            pending = PendingWrite(table, payload, str(exc), self._now())
            self.outbox_path.parent.mkdir(parents=True, exist_ok=True)
            with self.outbox_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(asdict(pending), default=str) + "\n")
            return False

    def log_tool_call(
        self,
        session_id: str,
        tool_name: str,
        args: dict[str, Any],
        output: Any,
        cost_usd: float,
    ) -> bool:
        payload = {
            "session_id": session_id,
            "tool_name": tool_name,
            "arguments_hash": self._args_hash(args),
            "cost_incurred": float(cost_usd),
        }
        return self._write("tool_execution_logs", payload)

    def log_loop_detection(
        self,
        session_id: str,
        loop_info: dict[str, Any],
        tool_name: str,
        fingerprint: str,
    ) -> bool:
        payload = {
            "session_id": session_id,
            "alert_type": str(loop_info.get("alert_type", "loop_detected")),
            "fingerprint": fingerprint,
            "cycle_length": int(loop_info.get("cycle_length", 1)),
        }
        return self._write("agent_alerts", payload)

    def pause_session(self, session_id: str, reason: str) -> bool:
        # The requested schema exposes is_paused; reason remains in the local outbox
        # only when the write fails because no reason column was specified.
        return self._update("agent_sessions", {"is_paused": True}, {"session_id": session_id}, reason=reason)

    def update_session_spend(self, session_id: str, current_spend: float) -> bool:
        return self._update("agent_sessions", {"current_spend": float(current_spend)}, {"session_id": session_id})

    def _update(self, table: str, values: dict[str, Any], filters: dict[str, Any], **context: Any) -> bool:
        try:
            query = self.client.table(table).update(values)
            for key, value in filters.items():
                query = query.eq(key, value)
            query.execute()
            return True
        except Exception as exc:  # noqa: BLE001 - network/client errors must be queued
            payload = {**values, **filters, **context}
            pending = PendingWrite(table, payload, str(exc), self._now())
            self.outbox_path.parent.mkdir(parents=True, exist_ok=True)
            with self.outbox_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(asdict(pending), default=str) + "\n")
            return False

    def record_decision(self, session_id: str, decision: dict[str, Any] | str, timestamp: str | None = None) -> bool:
        payload = {
            "session_id": session_id,
            "action": str(decision.get("action", "tool_call") if isinstance(decision, dict) else "tool_call"),
            "decision": json.dumps(decision, default=str) if isinstance(decision, dict) else str(decision),
            "timestamp": timestamp or self._now(),
        }
        return self._write("audit_events", payload)
