from __future__ import annotations

import os
from uuid import uuid4

from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from supabase import create_client

from langchain_handler import LoopBreakerHandler, LoopDetectedException
from supabase_logger import SupabaseLogger

load_dotenv()
session_id = os.getenv("SESSION_ID", str(uuid4()))
print(f"session_id={session_id}")
client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
logger = SupabaseLogger(client)
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
