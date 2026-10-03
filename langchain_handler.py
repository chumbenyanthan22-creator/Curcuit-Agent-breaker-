from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from agentbreaker_detector import Detector, ToolCall
from supabase_logger import SupabaseLogger


class LoopDetectedException(RuntimeError):
    def __init__(self, session_id: str, tool_name: str, fingerprint: str, cycle_length: int) -> None:
        self.session_id = session_id
        self.tool_name = tool_name
        self.fingerprint = fingerprint
        self.cycle_length = cycle_length
        super().__init__(f"Loop detected for {tool_name} after {cycle_length} identical calls")


@dataclass(frozen=True)
class HandlerResult:
    output: Any
    cost_usd: float


class LoopBreakerHandler:
    """Pre-dispatch handler for LangChain tools with Supabase event logging."""

    def __init__(self, session_id: str, logger: SupabaseLogger, detector: Detector | None = None, cost_per_call_usd: float = 0.0) -> None:
        self.session_id = session_id
        self.logger = logger
        self.detector = detector or Detector()
        self.cost_per_call_usd = float(cost_per_call_usd)
        self.current_spend = 0.0

    def invoke(self, tool_name: str, args: dict[str, Any], execute: Callable[[dict[str, Any]], Any]) -> HandlerResult:
        call = ToolCall(self.session_id, tool_name, args)
        decision = self.detector.evaluate(call)
        self.logger.record_decision(self.session_id, {"action": tool_name, "decision": decision.action, "reason": decision.reason})
        if decision.action == "blocked":
            info = {"alert_type": "loop_detected", "cycle_length": self.detector.loop_threshold}
            self.logger.log_loop_detection(self.session_id, info, tool_name, call.fingerprint)
            self.logger.pause_session(self.session_id, decision.reason)
            raise LoopDetectedException(self.session_id, tool_name, call.fingerprint, self.detector.loop_threshold)
        output = execute(args)
        self.current_spend += self.cost_per_call_usd
        self.logger.log_tool_call(self.session_id, tool_name, args, output, self.cost_per_call_usd)
        self.logger.update_session_spend(self.session_id, self.current_spend)
        return HandlerResult(output=output, cost_usd=self.cost_per_call_usd)

    # Callback-shaped aliases for LangChain integrations.
    def on_loop(self, tool_name: str, loop_info: dict[str, Any], fingerprint: str) -> None:
        self.logger.log_loop_detection(self.session_id, loop_info, tool_name, fingerprint)
        self.logger.pause_session(self.session_id, str(loop_info.get("reason", "loop detected")))

    def on_tool_end(self, tool_name: str, args: dict[str, Any], output: Any, cost_usd: float) -> None:
        self.current_spend += float(cost_usd)
        self.logger.log_tool_call(self.session_id, tool_name, args, output, cost_usd)
        self.logger.update_session_spend(self.session_id, self.current_spend)
