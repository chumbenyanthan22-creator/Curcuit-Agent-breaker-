alter table public.tool_execution_logs
  add column if not exists model_name varchar,
  add column if not exists output_tokens_estimated integer,
  add column if not exists agent_id uuid references public.agents(id);

create index if not exists tool_execution_logs_executed_at_idx on public.tool_execution_logs(executed_at);
create index if not exists tool_execution_logs_agent_id_idx on public.tool_execution_logs(agent_id);
