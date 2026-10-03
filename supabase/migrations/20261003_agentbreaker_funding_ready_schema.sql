create extension if not exists pgcrypto;

create table if not exists public.workspaces (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  plan text not null default 'demo',
  created_at timestamptz not null default now()
);

create table if not exists public.agents (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  slug text not null,
  name text not null,
  description text not null default '',
  status text not null default 'active' check (status in ('active','paused','review')),
  agent_class text not null default 'standard' check (agent_class in ('standard','privileged')),
  risk_level text not null default 'low' check (risk_level in ('low','medium','high','critical')),
  budget_cents integer not null default 0 check (budget_cents >= 0),
  tool_calls integer not null default 0 check (tool_calls >= 0),
  last_seen_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (workspace_id, slug)
);

create table if not exists public.policies (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  title text not null,
  description text not null default '',
  scope text not null default 'all agents',
  enabled boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.approvals (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  agent_id uuid references public.agents(id) on delete set null,
  reference text not null,
  action text not null,
  detail text not null default '',
  risk_level text not null default 'medium' check (risk_level in ('low','medium','high','critical')),
  status text not null default 'pending' check (status in ('pending','approved','blocked')),
  requested_at timestamptz not null default now(),
  decided_at timestamptz,
  decided_by text
);

create table if not exists public.audit_events (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  agent_id uuid references public.agents(id) on delete set null,
  agent_name text not null,
  action text not null,
  detail text not null default '',
  outcome text not null check (outcome in ('allowed','blocked','approval')),
  risk_level text not null default 'low' check (risk_level in ('low','medium','high','critical')),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists agents_workspace_idx on public.agents(workspace_id);
create index if not exists policies_workspace_idx on public.policies(workspace_id);
create index if not exists approvals_workspace_status_idx on public.approvals(workspace_id, status);
create index if not exists audit_workspace_created_idx on public.audit_events(workspace_id, created_at desc);

alter table public.workspaces enable row level security;
alter table public.agents enable row level security;
alter table public.policies enable row level security;
alter table public.approvals enable row level security;
alter table public.audit_events enable row level security;

insert into public.workspaces (id, slug, name, plan)
values ('11111111-1111-1111-1111-111111111111', 'acme-prod-7f29', 'Acme Systems', 'demo')
on conflict (id) do update set name = excluded.name, plan = excluded.plan;

insert into public.agents (id, workspace_id, slug, name, description, status, agent_class, risk_level, budget_cents, tool_calls, last_seen_at)
values
('21111111-1111-1111-1111-111111111111','11111111-1111-1111-1111-111111111111','invoice','Invoice Agent','Reads invoices, matches purchase orders, and prepares payment drafts.','active','privileged','high',200,1284,now() - interval '18 seconds'),
('22222222-2222-2222-2222-222222222222','11111111-1111-1111-1111-111111111111','support','Support Resolution Agent','Resolves tickets, drafts replies, and routes sensitive customer issues.','active','standard','medium',50,8921,now() - interval '34 seconds'),
('23333333-3333-3333-3333-333333333333','11111111-1111-1111-1111-111111111111','vendor','Vendor Verification Agent','Verifies supplier identity, registration, and compliance evidence.','review','privileged','critical',125,642,now() - interval '2 minutes')
on conflict (id) do update set name = excluded.name, status = excluded.status, tool_calls = excluded.tool_calls, last_seen_at = excluded.last_seen_at;

insert into public.policies (id, workspace_id, title, description, scope, enabled)
values
('31111111-1111-1111-1111-111111111111','11111111-1111-1111-1111-111111111111','Privileged action approval','Pause financial mutations and permission changes until a verified operator approves.','Privileged agents',true),
('32222222-2222-2222-2222-222222222222','11111111-1111-1111-1111-111111111111','Tool-call budget guard','Stop sessions that exceed the assigned dollar or tool-call budget.','All agents',true),
('33333333-3333-3333-3333-333333333333','11111111-1111-1111-1111-111111111111','Loop and no-progress detection','Block repeated tool sequences when state or output does not advance.','All agents',true),
('34444444-4444-4444-4444-444444444444','11111111-1111-1111-1111-111111111111','Tool access allowlist','Allow only approved tools and schemas for each registered agent.','All tool calls',true),
('35555555-5555-5555-5555-555555555555','11111111-1111-1111-1111-111111111111','External data export','Require approval before sensitive records leave the trusted workspace.','Data-handling tools',false)
on conflict (id) do update set enabled = excluded.enabled, updated_at = now();

insert into public.approvals (id, workspace_id, agent_id, reference, action, detail, risk_level, status, requested_at)
values
('41111111-1111-1111-1111-111111111111','11111111-1111-1111-1111-111111111111','21111111-1111-1111-1111-111111111111','APR-2048','create_draft_payment','₹148,000 to Helius Components','high','pending',now() - interval '1 minute'),
('42222222-2222-2222-2222-222222222222','11111111-1111-1111-1111-111111111111','22222222-2222-2222-2222-222222222222','APR-2044','issue_refund','₹12,500 refund for ticket #4819','high','pending',now() - interval '8 minutes'),
('43333333-3333-3333-3333-333333333333','11111111-1111-1111-1111-111111111111','23333333-3333-3333-3333-333333333333','APR-2037','share_compliance_record','Share with new banking partner','critical','pending',now() - interval '14 minutes')
on conflict (id) do update set status = excluded.status, detail = excluded.detail;

insert into public.audit_events (id, workspace_id, agent_id, agent_name, action, detail, outcome, risk_level, created_at)
values
('51111111-1111-1111-1111-111111111111','11111111-1111-1111-1111-111111111111','21111111-1111-1111-1111-111111111111','Invoice Agent','create_draft_payment','₹148,000 vendor payment draft','approval','high',now() - interval '1 minute'),
('52222222-2222-2222-2222-222222222222','11111111-1111-1111-1111-111111111111','22222222-2222-2222-2222-222222222222','Support Resolution Agent','update_ticket','Ticket #4821 marked resolved','allowed','low',now() - interval '3 minutes'),
('53333333-3333-3333-3333-333333333333','11111111-1111-1111-1111-111111111111','23333333-3333-3333-3333-333333333333','Vendor Verification Agent','export_vendor_data','External destination blocked','blocked','critical',now() - interval '6 minutes'),
('54444444-4444-4444-4444-444444444444','11111111-1111-1111-1111-111111111111','21111111-1111-1111-1111-111111111111','Invoice Agent','read_invoice','Invoice INV-2048 parsed','allowed','low',now() - interval '8 minutes'),
('55555555-5555-5555-5555-555555555555','11111111-1111-1111-1111-111111111111','22222222-2222-2222-2222-222222222222','Support Resolution Agent','send_email','Reply sent to customer','allowed','medium',now() - interval '12 minutes'),
('56666666-6666-6666-6666-666666666666','11111111-1111-1111-1111-111111111111','23333333-3333-3333-3333-333333333333','Vendor Verification Agent','fetch_gst_record','Verification source responded','allowed','medium',now() - interval '18 minutes'),
('57777777-7777-7777-7777-777777777777','11111111-1111-1111-1111-111111111111','21111111-1111-1111-1111-111111111111','Invoice Agent','read_invoice','Loop threshold reached','blocked','high',now() - interval '23 minutes')
on conflict (id) do nothing;

create policy "demo workspace readable" on public.workspaces for select to anon, authenticated using (id = '11111111-1111-1111-1111-111111111111');
create policy "demo agents readable" on public.agents for select to anon, authenticated using (workspace_id = '11111111-1111-1111-1111-111111111111');
create policy "demo policies readable" on public.policies for select to anon, authenticated using (workspace_id = '11111111-1111-1111-1111-111111111111');
create policy "demo approvals readable" on public.approvals for select to anon, authenticated using (workspace_id = '11111111-1111-1111-1111-111111111111');
create policy "demo audit readable" on public.audit_events for select to anon, authenticated using (workspace_id = '11111111-1111-1111-1111-111111111111');
