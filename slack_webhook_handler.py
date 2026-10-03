from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Form, HTTPException

from agentbreaker_detector import Detector
from supabase_logger import SupabaseLogger


@dataclass
class SessionControl:
    detector: Detector
    logger: SupabaseLogger


app = FastAPI(title="AgentBreaker Slack webhook")
_sessions: dict[str, SessionControl] = {}


def register_session(session_id: str, detector: Detector, logger: SupabaseLogger) -> None:
    _sessions[session_id] = SessionControl(detector=detector, logger=logger)


def _payload_data(payload: str) -> dict[str, Any]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid Slack payload") from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Invalid Slack payload")
    return data


@app.post("/webhook/slack")
async def slack_button(payload: str = Form(...)) -> dict[str, str]:
    data = _payload_data(payload)
    actions = data.get("actions") or []
    if not actions:
        raise HTTPException(status_code=400, detail="Missing Slack action")
    action = actions[0]
    action_id = action.get("action_id")
    try:
        value = json.loads(action.get("value", "{}"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid action value") from exc
    session_id = value.get("session_id")
    control = _sessions.get(session_id)
    if not session_id or control is None:
        raise HTTPException(status_code=404, detail="Unknown or expired session")
    if action_id == "agentbreaker_continue":
        control.detector.reset(session_id)
        return {"text": f"AgentBreaker detector reset for session {session_id}. Continue approved."}
    if action_id == "agentbreaker_kill":
        control.logger.pause_session(session_id, "Killed from Slack")
        return {"text": f"AgentBreaker session {session_id} remains paused. Kill recorded."}
    raise HTTPException(status_code=400, detail="Unsupported Slack action")
