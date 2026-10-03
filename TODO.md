# AgentBreaker prototype outcomes

- **Deliver the desktop-first AgentBreaker application shell with dark navy enterprise security-console styling and left navigation for Overview, Agent Registry, Policies, Approvals, Audit Trail, and Settings.** The prototype must keep all six destinations visible in the left navigation and allow the user to switch sections without a page reload.
- **Deliver the Overview dashboard with functional seeded metrics and monitoring surfaces.** Show KPI cards for Protected Agents, Actions Today, Blocked Actions, and Spend Guarded; include a working time-range control that changes displayed mock metrics; show a live activity feed, status and agent filters, a risk distribution visualization, and a right-side incident/approval panel.
- **Deliver the Agent Registry and clickable agent detail view.** Seed Invoice Agent, Support Resolution Agent, and Vendor Verification Agent with status, class, risk level, budget, and recent activity; selecting an agent must open a governance profile with budget context, recent actions, and operating status.
- **Deliver the Policies section with representative runtime guardrails and client-side controls.** Show policy rules for tool access, approval thresholds, spend limits, loop detection, and data handling; toggling a policy must immediately reflect its active or paused state.
- **Deliver approval and response interactions.** Users must be able to approve or block a pending action, and trigger a clearly presented emergency stop; the resulting state must be reflected in the activity feed and approval queue.
- **Deliver Audit Trail and Settings sections with realistic seeded records and representative configuration controls.** Keep all data and interactions client-side without authentication or external services.
- **Deliver a working static route manifest and project metadata.** Serve `/manus-routes.json` for the root page and include project logo metadata before checkpointing.

## Cost tracking

- Add estimate-based `CostCalculator` with config-loaded model pricing.
- Persist estimated output tokens, model name, and calculated cost for every tool execution.
- Increment `agent_sessions.current_spend_usd` from logged tool costs.
- Add cached daily spend aggregation and dashboard cost trend/per-call cost display.
