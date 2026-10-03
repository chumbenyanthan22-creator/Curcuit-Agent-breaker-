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
