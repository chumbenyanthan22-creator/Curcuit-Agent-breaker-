create table if not exists public.agent_sessions (
  session_id uuid primary key,
  company_id uuid,
  max_budget_usd numeric,
  current_spend_usd numeric,
  is_paused boolean,
  created_at timestamp
);

create table if not exists public.tool_execution_logs (
  id bigserial primary key,
  session_id uuid references public.agent_sessions(session_id),
  tool_name varchar,
  arguments_hash varchar,
  cost_incurred numeric,
  executed_at timestamp
);

create table if not exists public.agent_alerts (
  id bigserial primary key,
  session_id uuid references public.agent_sessions(session_id),
  alert_type varchar,
  fingerprint varchar,
  cycle_length int,
  created_at timestamp
);
