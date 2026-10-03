from pathlib import Path

import pytest

from agentbreaker_detector import Detector
from langchain_handler import LoopBreakerHandler, LoopDetectedException
from supabase_logger import SupabaseLogger


class Query:
    def __init__(self, store, table, fail=False):
        self.store, self.table_name, self.fail = store, table, fail
        self.operation, self.payload, self.filters = None, None, {}

    def select(self, columns):
        return self

    def limit(self, count):
        return self

    def upsert(self, payload, on_conflict=None):
        self.operation, self.payload = "upsert", payload
        return self

    def insert(self, payload):
        self.operation, self.payload = "insert", payload
        return self

    def update(self, payload):
        self.operation, self.payload = "update", payload
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def execute(self):
        if self.fail:
            raise ConnectionError("Supabase unavailable")
        if self.operation is not None:
            self.store.append((self.operation, self.table_name, self.payload, self.filters))
        return {"data": [self.payload]}


class FakeClient:
    def __init__(self, fail=False):
        self.store, self.fail = [], fail

    def table(self, name):
        return Query(self.store, name, self.fail)


def test_logger_reports_schema_ready(tmp_path: Path):
    assert SupabaseLogger(FakeClient(), tmp_path / "outbox.jsonl").schema_ready


def test_session_initialization_writes_expected_schema(tmp_path: Path):
    client = FakeClient()
    assert SupabaseLogger(client, tmp_path / "outbox.jsonl").ensure_session("s1")
    assert client.store[0][0] == "upsert" and client.store[0][1] == "agent_sessions"
    assert client.store[0][2]["current_spend_usd"] == 0.0


def test_tool_call_writes_expected_schema(tmp_path: Path):
    client = FakeClient()
    assert SupabaseLogger(client, tmp_path / "outbox.jsonl").log_tool_call("s1", "read_invoice", {"id": 1}, "ok", 0.01)
    operation, table, payload, _ = client.store[0]
    assert operation == "insert" and table == "tool_execution_logs"
    assert payload["session_id"] == "s1" and payload["tool_name"] == "read_invoice"


def test_loop_write_has_fingerprint_and_cycle_length(tmp_path: Path):
    client = FakeClient()
    logger = SupabaseLogger(client, tmp_path / "outbox.jsonl")
    assert logger.log_loop_detection("s1", {"cycle_length": 3}, "read_invoice", "abc")
    assert client.store[0][1] == "agent_alerts"
    assert client.store[0][2]["fingerprint"] == "abc"


def test_pause_updates_session(tmp_path: Path):
    client = FakeClient()
    assert SupabaseLogger(client, tmp_path / "outbox.jsonl").pause_session("s1", "loop")
    assert client.store[0][1] == "agent_sessions"
    assert client.store[0][2] == {"is_paused": True}


def test_failed_write_goes_to_outbox(tmp_path: Path):
    outbox = tmp_path / "outbox.jsonl"
    assert not SupabaseLogger(FakeClient(fail=True), outbox).record_decision("s1", "blocked")
    assert outbox.exists() and "audit_events" in outbox.read_text()


def test_handler_logs_calls_spend_and_loop(tmp_path: Path):
    client = FakeClient()
    logger = SupabaseLogger(client, tmp_path / "outbox.jsonl")
    handler = LoopBreakerHandler("s1", logger, Detector(loop_threshold=3), cost_per_call_usd=0.1)
    for _ in range(2):
        handler.invoke("read_invoice", {"id": "INV-1"}, lambda args: "ok")
    with pytest.raises(LoopDetectedException):
        handler.invoke("read_invoice", {"id": "INV-1"}, lambda args: "should-not-run")
    tables = [entry[1] for entry in client.store]
    assert tables.count("tool_execution_logs") == 2
    assert "agent_alerts" in tables
    assert "agent_sessions" in tables
    assert handler.current_spend == 0.2
