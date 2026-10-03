from __future__ import annotations

import time

from slack_alerter import SlackAlerter


session_id = "demo-slack-session"
alerter = SlackAlerter.from_env()
loop_info = {
    "alert_type": "loop_detected",
    "loop_type": "repeat",
    "fingerprint": "9cf8fe2530d8a1b2c3d4e5f6",
    "cycle_length": 3,
}
print(f"Simulating loop detection for session_id={session_id}")
alerter.alert_loop(session_id, loop_info, "read_invoice")
print("Slack alert scheduled without blocking the detector.")
if alerter.webhook_url:
    time.sleep(0.2)  # allow the daemon thread to submit in this short-lived demo
else:
    print("Dry run: set SLACK_WEBHOOK_URL to deliver the Block Kit message.")
