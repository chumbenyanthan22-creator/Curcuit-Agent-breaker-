import pytest

from agentbreaker_detector import Detector, EnforcementHandler, ToolCall


def call(tool="read_invoice", args=None, agent="agent-1"):
    return ToolCall(agent, tool, args or {"invoice_id": "INV-1"})


def test_first_call_allowed():
    assert Detector().evaluate(call()).action == "allowed"


def test_second_identical_call_allowed():
    detector = Detector()
    detector.evaluate(call())
    assert detector.evaluate(call()).action == "allowed"


def test_third_identical_call_blocked():
    detector = Detector()
    for _ in range(2):
        detector.evaluate(call())
    decision = detector.evaluate(call())
    assert decision.action == "blocked"


def test_block_reason_mentions_no_progress():
    detector = Detector()
    for _ in range(3):
        decision = detector.evaluate(call())
    assert "no progress" in decision.reason.lower()


def test_loop_policy_is_reported():
    detector = Detector()
    for _ in range(3):
        decision = detector.evaluate(call())
    assert "loop_and_no_progress_detection" in decision.matched_policies


def test_blocked_risk_is_high():
    detector = Detector()
    for _ in range(3):
        decision = detector.evaluate(call())
    assert decision.risk_score >= 80


def test_different_arguments_do_not_trigger():
    detector = Detector()
    detector.evaluate(call(args={"invoice_id": "INV-1"}))
    detector.evaluate(call(args={"invoice_id": "INV-2"}))
    assert detector.evaluate(call(args={"invoice_id": "INV-3"})).action == "allowed"


def test_different_tools_do_not_trigger():
    detector = Detector()
    detector.evaluate(call("read_invoice"))
    detector.evaluate(call("fetch_gst_record"))
    assert detector.evaluate(call("read_invoice")).action == "allowed"


def test_different_agents_are_isolated():
    detector = Detector()
    for _ in range(3):
        detector.evaluate(call(agent="agent-a"))
    assert detector.evaluate(call(agent="agent-b")).action == "allowed"


def test_reset_clears_history():
    detector = Detector()
    detector.evaluate(call())
    detector.evaluate(call())
    detector.reset("agent-1")
    assert detector.evaluate(call()).action == "allowed"


def test_threshold_is_configurable():
    detector = Detector(loop_threshold=4)
    for _ in range(3):
        assert detector.evaluate(call()).action == "allowed"
    assert detector.evaluate(call()).action == "blocked"


def test_invalid_threshold_is_rejected():
    with pytest.raises(ValueError):
        Detector(loop_threshold=1)


def test_handler_executes_allowed_call():
    calls = []
    result = EnforcementHandler().handle(call(), lambda item: calls.append(item.tool) or "done")
    assert result.executed is True
    assert result.output == "done"
    assert calls == ["read_invoice"]


def test_handler_does_not_execute_blocked_call():
    calls = []
    handler = EnforcementHandler()
    for _ in range(3):
        result = handler.handle(call(), lambda item: calls.append(item.tool))
    assert result.executed is False
    assert calls == ["read_invoice", "read_invoice"]


def test_handler_returns_block_decision():
    handler = EnforcementHandler()
    for _ in range(3):
        result = handler.handle(call(), lambda item: None)
    assert result.decision.action == "blocked"


def test_handler_preserves_tool_arguments():
    seen = []
    args = {"invoice_id": "INV-99", "include_lines": True}
    EnforcementHandler().handle(call(args=args), lambda item: seen.append(item.arguments))
    assert seen == [args]


def test_empty_arguments_are_supported():
    assert Detector().evaluate(call(args={})).action == "allowed"


def test_fingerprint_is_stable_for_key_order():
    left = call(args={"a": 1, "b": 2}).fingerprint
    right = call(args={"b": 2, "a": 1}).fingerprint
    assert left == right


def test_fingerprint_changes_for_agent():
    assert call(agent="a").fingerprint != call(agent="b").fingerprint


def test_fingerprint_changes_for_tool():
    assert call("read_invoice").fingerprint != call("send_email").fingerprint
