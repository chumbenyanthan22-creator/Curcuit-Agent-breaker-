# AgentBreaker prototype plan

## Product direction
AgentBreaker is presented as the runtime safety and governance layer for enterprise AI agents. The prototype is a clickable desktop-first control plane that makes the key product promise legible: every proposed tool action is evaluated against identity, permissions, risk, budget, loop behavior, and approval rules before being allowed, blocked, or paused, with a complete audit record.

## Design direction
- **Design movement:** dark operations-console / cybernetic control-room UI, restrained rather than gamer-like.
- **Core principles:** visible control, calm urgency, evidence over decoration, progressive disclosure.
- **Color philosophy:** deep ink/navy surfaces make the product feel trusted and mission-critical; mint/teal is the ownable "safe" action color; amber and coral are reserved for approvals, warnings, and blocks.
- **Layout paradigm:** persistent left rail + top command bar + asymmetric dashboard: dense primary workspace and a narrow right-side incident/approval rail.
- **Signature elements:** status dots with soft glow, thin grid/radar texture, and a persistent "runtime enforcement" banner.
- **Interaction philosophy:** every control should communicate a decision state; approval and emergency-stop actions should feel immediate and auditable.
- **Animation:** subtle pulse on live monitoring, short row highlight after an action, no decorative motion that competes with risk signals.
- **Typography:** Inter/system UI for high legibility, compact uppercase labels for metadata, larger numeric metrics with tabular-feeling emphasis.
- **Brand essence:** the neutral control layer that lets teams deploy autonomous agents without surrendering authority. Personality: precise, vigilant, composed.
- **Brand voice:** direct and operational. Example lines: "Bounded autonomy, visible by default." and "Stop risky actions before they leave the control boundary."
- **Wordmark/mark:** shield outline intersected by a break/interrupt glyph; represented in the prototype by a shield mark and a mint break accent.
- **Signature brand color:** AgentBreaker mint `#72F6C3`.

## Implementation
- Reuse the initialized React/Vite starter.
- Keep all data client-side with seeded mock data and React state.
- One route (`/`) with view switching in the application shell so the prototype feels like a real product without requiring authentication or a backend.
- Build the major surfaces as reusable arrays and inline components in `Home.tsx` for speed; keep the global visual system in `index.css`.
- Provide `/manus-routes.json` with the root route.

## Project structure
- `client/src/pages/Home.tsx`: application shell, mock data, views, and interactions.
- `client/src/index.css`: visual system, layout primitives, responsive behavior, and state styling.
- `client/public/manus-routes.json`: route manifest for the Webdev runtime.
- `app.config.ts`: durable logo metadata for the project.
- `TODO.md`: outcome-focused acceptance clauses from the approved blueprint.
