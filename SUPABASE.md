# Supabase integration

AgentBreaker is connected to the Supabase project `AgentBreaker` in `ap-south-1`.

## Live data model

- `workspaces` — tenant/workspace identity
- `agents` — registered agent fleet, budgets, risk, and status
- `policies` — runtime guardrails and enablement
- `approvals` — human-in-the-loop decisions
- `audit_events` — append-oriented evidence of agent activity

The migration and demo seed are stored in `supabase/migrations/20261003_agentbreaker_funding_ready_schema.sql`.

## Frontend connection

The dashboard reads the demo workspace from Supabase using the browser-safe publishable key. It shows `Supabase synced` when the live reads succeed and falls back to seed data if the network is unavailable.

For deployment, set:

```sh
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
```

The publishable key is safe for browser use only when Row Level Security remains enabled. Do not place a Supabase service-role key in frontend code.

## Current prototype boundary

The dashboard’s approval, policy-toggle, and emergency-stop interactions remain local demo state. A production version should add authenticated users, workspace-scoped RLS policies, server-side approval mutations, append-only audit ingestion, and realtime subscriptions before handling real financial or operational actions.

## Detector pipeline

The applied migration `supabase/migrations/001_create_detector_tables.sql` adds:

- `agent_sessions`
- `tool_execution_logs`
- `agent_alerts`

`SupabaseLogger` checks these tables at startup, connects from `SUPABASE_URL` and `SUPABASE_KEY` when no client is injected, and writes failures to `.agentbreaker-outbox.jsonl`. Database DDL is applied through the migration, not executed by the runtime with a public key.

The real proof agent wrote session `bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb` with 2 tool executions, 3 loop alerts, `$0.02` spend, and `is_paused = true`. The dashboard now reads `agent_alerts` and displays the caught loops as live activity.

## RLS hardening required

Supabase currently reports the three detector tables as RLS-disabled. This is acceptable only for the temporary demo proof and exposes rows to clients using the anon key. Before production, enable RLS and add authenticated, workspace/session-scoped policies. Do not use the anon key for unrestricted server writes; use a server-side service-role secret or protected backend route.

## Cost telemetry

Migration `supabase/migrations/002_cost_tracking.sql` adds `model_name`, `output_tokens_estimated`, and optional `agent_id` to `tool_execution_logs`. `CostCalculator` estimates output tokens as roughly four characters per token and applies rates from `pricing_config.json` or `AGENTBREAKER_PRICING_CONFIG`; it never calls a model provider. Each `SupabaseLogger.log_tool_call()` writes the calculated cost and increments `agent_sessions.current_spend_usd`. `AggregateSpendingView` groups costs by UTC day and agent/session and caches results for five minutes.
