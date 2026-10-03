from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    agent_id: str
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(
            {"agent_id": self.agent_id, "tool": self.tool, "arguments": self.arguments},
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode()
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    risk_score: int
    matched_policies: tuple[str, ...] = ()


class Detector:
    """Small deterministic pre-dispatch guard for repeat/no-progress behavior."""

    def __init__(self, loop_threshold: int = 3) -> None:
        if loop_threshold < 2:
            raise ValueError("loop_threshold must be at least 2")
        self.loop_threshold = loop_threshold
        self._recent: dict[str, list[str]] = {}

    def evaluate(self, call: ToolCall) -> Decision:
        history = self._recent.setdefault(call.agent_id, [])
        history.append(call.fingerprint)
        history[:] = history[-self.loop_threshold :]
        if len(history) == self.loop_threshold and len(set(history)) == 1:
            return Decision(
                action="blocked",
                reason="Repeated identical tool sequence made no progress",
                risk_score=92,
                matched_policies=("loop_and_no_progress_detection",),
            )
        return Decision(action="allowed", reason="No blocking policy matched", risk_score=8)

    def reset(self, agent_id: str) -> None:
        self._recent.pop(agent_id, None)
