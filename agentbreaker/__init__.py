"""Loop detection and cost tracking for LangChain agents."""

from .detector import Decision, Detector, ToolCall
from .handler import EnforcementHandler, EnforcementResult
from .langchain_handler import HandlerResult, LoopBreakerHandler, LoopDetectedException

# Preferred public name; retain Detector as a compatibility alias.
LoopDetector = Detector

__all__ = [
    "Decision",
    "Detector",
    "EnforcementHandler",
    "EnforcementResult",
    "HandlerResult",
    "LoopBreakerHandler",
    "LoopDetectedException",
    "LoopDetector",
    "ToolCall",
]
