# Architecture and implementation boundaries

## System shape

```text
Invoice / payroll / till events
          │
          ▼
    n8n workflows ── authenticated invoice event ──► Invoice Agent service
                                                        │ normalized idempotent intent
                                                        ▼
Next.js dashboard ── authenticated API ──► Mandate API controllers
                                                  │
                          ┌───────────────────────┴────────────────────┐
                          ▼                                            ▼
                 Application services                         Readiness/health
             mandate / policy / intent / audit                         │
                │             │                                       ▼
                ▼             ▼                                Postgres / XRPL RPC
           repositories   rail ports                                  ▲
                              │                                        │
                              └──── XRPL Testnet adapter ─────────────┘
                                      policy signer only
```

The invoice agent runs as a separate container and receives no database URL or XRPL signing seed. It can submit intents only. The Mandate API independently evaluates the active human-defined policy and then invokes the XRPL adapter. The policy evaluator and signing adapter currently run inside the same trusted API process; the important MVP boundary is that the agent cannot access or bypass that process's signer. A hardened production design should split policy authorization and signing into separately deployed, narrowly scoped services.

Autonomy flow: n8n forwards an approved structured invoice event; the standalone invoice agent normalizes it and calls the intent API without waiting for per-payment human approval when the mandate permits it. The API independently rechecks the mandate and is the only component allowed to invoke the XRPL signer. Human approval is reserved for configured exceptions such as high-value transfers. This MVP agent is deterministic and event-driven, not an LLM invoice reader.

## Python MVC / clean architecture layout

```text
backend/app/
  main.py
  config.py
  controllers/       HTTP parsing, auth dependency, response mapping
  schemas/           Pydantic request/response contracts
  services/          mandate, policy, intent orchestration, approvals, audit
  models/domain.py   framework-independent entities, value objects and enums
  models/orm.py      SQLAlchemy persistence mapping
  repositories/      mandate, payee, intent, decision, payment, audit persistence
  integrations/
    rails/           Rail interface and XRPL testnet implementation
    fx/              Firm quote interface (only when a real source is selected)
  agent/             separate invoice-agent API/client; no signer or policy bypass
  db/                engine, session and unit-of-work setup
```

Suggested services: `MandateService` validates/version-controls changes; `PayeeService` manages allowed counterparties; `PolicyService` is a pure deterministic evaluator; `IntentService` handles idempotency, policy decisions and lifecycle; `ApprovalService` records authorized human actions; `PaymentOrchestrator` reserves budget and dispatches approved intents; `AuditService` appends events. Controllers should not directly query ORM rows or call XRPL.

Suggested repositories: `MandateRepository`, `PayeeRepository`, `IntentRepository`, `ApprovalRepository`, `PaymentAttemptRepository`, `AuditRepository`. Repositories return domain objects or explicit persistence results, not FastAPI responses.

## Data and lifecycle

Money uses `Decimal`/SQL `NUMERIC`; asset identity includes code, issuer where applicable, and network. Store UTC timestamps and use the organization's configured timezone only for daily-budget boundaries. The initial single-tenant demo can use a fixed demo organization, but persistent records should carry an `organization_id` before exposing the service to more than one organization.

Intent lifecycle:

```text
received ──policy──► blocked
    │
    ├───────────────► needs_approval ──human approve──► authorized
    │                                              │
    └────────policy allowed────────────────────────┘
                                                   ▼
                                               submitted
                                              /         \
                                         settled       failed
```

Maintain separate policy decision and payment attempt records. Retain an immutable decision snapshot referencing the mandate version so later mandate edits do not rewrite the explanation for a past decision. For an in-flight transaction, reserve daily budget atomically; release the reservation on definitive failure. Use a database transaction and unique constraint on organization plus idempotency key to prevent duplicate processing.

## Payment rail boundary

Define a rail port around `quote`, `submit`, `get_status` and (where supported) `cancel`; each operation returns normalized result types while preserving provider references. XRPL implements only the capabilities it can support. A bank/BCB-style adapter must not be added until a real commercial relationship, published API documentation, credentials and sandbox are supplied. Likewise, a DEX indicative rate is not an executable fiat FX quote. Keep liquidity checks and FX conversion unavailable until their provider semantics are known. No provider/quote must not silently select a route; either pay the invoice's explicit asset without conversion or block and explain what is missing.

For XRPL issued assets, configure the exact currency code, issuer and network. Validate the destination and ensure the treasury has the needed trustline/balance before submission. Treat `submit` as a transition to submitted; confirm ledger validation and inspect `meta.TransactionResult` before marking settled. `tesSUCCESS` means applied; `tec` results are failed/applied outcomes that can still consume a fee, so store the exact engine result and fee. A hash by itself is not proof of successful settlement. Never silently fall back from testnet to mainnet. Keep the signing service and secret isolated from the agent and public API process where practical; for the hackathon, at minimum load a test-only signer secret only in the rail adapter process.

For a dedicated demo account, an offline CFO/master wallet can install a policy-service regular key and later revoke it with a validated `SetRegularKey` transaction. This on-ledger revocation is a coarse emergency stop, not a spending limit: the application policy must enforce caps and allowlists before each signature. Demonstrate both the independent policy block and, if time permits, the validated key revocation. Do not suggest that revoking a flag stored in the database revokes ledger authority.

## Trust and operational controls

1. The agent is untrusted and proposes/initiates structured intents. Its natural-language explanation is stored as context, not interpreted as permission. Normal eligible transfers should execute without a human click to satisfy the autonomy criterion.
2. The policy service fails closed if the mandate, payee, asset, limits or freshness cannot be established.
3. The signer is not available to the agent runtime, frontend, n8n, logs or exception payloads.
4. n8n webhooks authenticate the sender, validate payload size/schema, use idempotency and never carry private keys.
5. Dashboard mutation and approval endpoints require authenticated roles before real funds are possible. A demo secret header is not production authentication.
6. Audit data is append-only at the application level. Do not put wallet seeds, API tokens, full bank details or unnecessary personal data in it.
7. API kill switch and on-ledger signer revocation are distinct controls. The policy block is a per-intent authorization control; regular-key revocation is an emergency credential control. Report each result accurately and retain an offline master-key recovery procedure.
8. Configure per-environment XRPL URL, issuers and asset IDs explicitly; reject missing or inconsistent values at startup for payment operations.

## HTTP and integration contracts

Use request/response Pydantic schemas with validation and stable error codes. `POST /intents` requires an idempotency key and returns intent ID, mandate version, policy verdict, status, detail and optional XRPL hash/result. API version is `/api/v1`. List endpoints are paginated server-side. Controllers call services and map domain errors to HTTP status codes; no policy logic lives in routes. Operator routes use `X-Admin-API-Key`; the intent endpoint accepts separate agent or n8n credentials.

n8n authenticates one source event and normalizes it for `POST /api/v1/agent/invoices`. The agent derives a stable idempotency key from the invoice ID, then submits the intent using its restricted agent credential. For the MVP, only `invoice-approved` is wired; payroll batch and till settlement become separate workflow adapters after this contract is proven. Retry the same invoice ID on timeout; the API's idempotency record prevents a second payment attempt.

## Frontend direction

Use **Next.js (React + TypeScript)** for the product UI. Landing page sections: problem, controlled workflow, rails/integration boundary, auditability and a demo CTA. Use a subtle particle background as decorative presentation only; respect reduced-motion and provide a static fallback. The signed-in admin views are mandate/payee management, intent queue/detail, approvals, audit trail and kill-switch status. Use ApexCharts for admin aggregates only; do not fabricate live liquidity or market figures. Chart.js is unnecessary if ApexCharts is selected.

The Next.js application in `src/frontend` includes the public landing page, first-owner email/password signup, login and password recovery, plus a session-protected dashboard for mandate/payee controls, approvals, intent detail and audit history. The dashboard uses an HTTP-only signed session and same-origin server routes; admin API keys and the n8n webhook secret stay server-side. A dashboard workflow panel can send a demo invoice through the active n8n webhook and blocks that demo while XRPL execution is enabled. ApexCharts plots persisted policy aggregates, and tsParticles is decorative with reduced-motion support. Routine workflow testing does not require hand-written API requests in a terminal.

## Current repository state

Implemented: FastAPI controllers/services/repositories for owner authentication, password reset, mandates, payees, idempotent intents, approvals, dashboard aggregates and payment audit; additive Alembic migrations; a separate event-driven invoice-agent container that has no signer seed and can submit only through the intent API; optional XRPL Testnet/Devnet submission with validated-result handling; a manual regular-key install/revoke script; Next.js landing, account recovery, dashboard and dashboard-triggered n8n workflow demo; and an importable n8n invoice webhook that calls the agent.

Still prototype/incomplete: the agent is deterministic and does not use an LLM to extract invoices or perform reasoning; the workspace/account flow is single-owner and single-tenant; `BUSINESS_TIMEZONE` is a single app setting; there is no team invite/RBAC/MFA/SSO; policy and signing share the FastAPI process; there is no fiat payout adapter, executable FX quote or live liquidity service; and mandate/payee configuration changes are versioned but not yet written to a general-purpose activity log. Password reset emails need SMTP configuration outside local development. XRPL execution defaults off and requires explicit wallet, issuer/trustline and regular-key setup. Runtime validation and the live demo remain for the user.
