from __future__ import annotations

import os
from uuid import uuid4

from dotenv import load_dotenv
from langchain_core.tools import StructuredTool

from langchain_handler import LoopBreakerHandler, LoopDetectedException
from slack_alerter import SlackAlerter
from supabase_logger import SupabaseLogger

load_dotenv()
session_id = os.getenv("SESSION_ID", str(uuid4()))
print(f"session_id={session_id}")
logger = SupabaseLogger(slack_alerter=SlackAlerter.from_env())
if not logger.schema_ready:
    raise RuntimeError(f"Missing Supabase tables: {', '.join(logger.missing_tables)}")
if not logger.ensure_session(session_id, max_budget_usd=10.0):
    raise RuntimeError("Could not initialize agent session")
handler = LoopBreakerHandler(session_id, logger, cost_per_call_usd=0.01)


def read_invoice(invoice_id: str) -> str:
    return f"invoice {invoice_id} read"


invoice_tool = StructuredTool.from_function(read_invoice, name="read_invoice", description="Read an invoice")
for attempt in range(1, 6):
    try:
        result = handler.invoke("read_invoice", {"invoice_id": "INV-2048"}, lambda args: invoice_tool.invoke(args))
        print(f"attempt={attempt} executed={True} output={result.output}")
    except LoopDetectedException as exc:
        print(f"attempt={attempt} executed={False} caught={exc}")
