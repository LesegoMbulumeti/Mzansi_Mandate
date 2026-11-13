# Next.js frontend

The planned UI is Next.js (React + TypeScript), with a public landing page and a finance dashboard. The application has not been scaffolded yet.

## Views

- Landing page: finance workflow pain, mandate controls, payment lifecycle, audit trail and demo CTA.
- Overview: mandate status, today's budget usage, pending approvals and recent payment outcomes.
- Mandate and payees: limits, expiry, permitted assets and approved counterparties.
- Intent queue/detail: source reference, policy outcome, human approval and rail status.
- Audit trail: searchable immutable decisions with transaction explorer links where available.

## UI choices

- Use CSS/canvas particles as decorative background only; support `prefers-reduced-motion` and static fallback.
- Use ApexCharts for dashboard aggregates after real API data is available. Avoid invented liquidity or market statistics.
- Keep API types aligned with FastAPI's OpenAPI schema. Do not put credentials or signer material in browser code.

Scaffold with `npx create-next-app@latest` using TypeScript and the App Router. See `../docs/ARCHITECTURE.md` and `../docs/PROBLEM.md` before implementing API calls.
