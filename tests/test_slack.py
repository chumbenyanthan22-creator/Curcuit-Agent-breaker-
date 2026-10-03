import json
import threading

from fastapi.testclient import TestClient

from agentbreaker_detector import Detector
from slack_alerter import SlackAlerter
from slack_webhook_handler import app, register_session


class Logger:
    def __init__(self):
        self.paused = []

    def pause_session(self, session_id, reason):
        self.paused.append((session_id, reason))
        return True


def test_block_kit_contains_continue_and_kill():
    payload = SlackAlerter._payload("s1", {"loop_type": "repeat", "fingerprint": "abc", "cycle_length": 3}, "read_invoice")
    actions = payload["attachments"][0]["blocks"][-1]["elements"]
    assert [item["action_id"] for item in actions] == ["agentbreaker_continue", "agentbreaker_kill"]
    assert actions[0]["style"] == "primary"
    assert actions[1]["style"] == "danger"


def test_alert_posts_on_background_thread(monkeypatch):
    called = threading.Event()
    alerter = SlackAlerter("https://example.invalid/webhook")

    def fake_post(payload):
        called.set()

    monkeypatch.setattr(alerter, "_post", fake_post)
    alerter.alert_loop("s1", {"cycle_length": 3}, "read_invoice")
    assert called.wait(1)


def test_continue_resets_detector():
    detector = Detector()
    logger = Logger()
    register_session("s-continue", detector, logger)
    for _ in range(2):
        detector.evaluate(__import__("agentbreaker_detector").ToolCall("s-continue", "read", {}))
    response = TestClient(app).post("/webhook/slack", data={"payload": json.dumps({"actions": [{"action_id": "agentbreaker_continue", "value": json.dumps({"session_id": "s-continue"})}]})})
    assert response.status_code == 200
    assert detector._recent == {}


def test_kill_pauses_session():
    detector = Detector()
    logger = Logger()
    register_session("s-kill", detector, logger)
    response = TestClient(app).post("/webhook/slack", data={"payload": json.dumps({"actions": [{"action_id": "agentbreaker_kill", "value": json.dumps({"session_id": "s-kill"})}]})})
    assert response.status_code == 200
    assert logger.paused == [("s-kill", "Killed from Slack")]
