from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .detector import Decision, Detector, ToolCall


@dataclass(frozen=True)
class EnforcementResult:
    decision: Decision
    executed: bool
    output: Any = None


class EnforcementHandler:
    def __init__(self, detector: Detector | None = None) -> None:
        self.detector = detector or Detector()

    def handle(self, call: ToolCall, execute: Callable[[ToolCall], Any]) -> EnforcementResult:
        decision = self.detector.evaluate(call)
        if decision.action == "blocked":
            return EnforcementResult(decision=decision, executed=False)
        return EnforcementResult(decision=decision, executed=True, output=execute(call))
