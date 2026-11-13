# Architecture and implementation boundaries

## System shape

```text
Invoice / payroll / till events
          │
          ▼
    n8n workflows ── signed/idempotent webhook ──┐
                                                  ▼
Next.js dashboard ── authenticated API ── FastAPI controllers
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

The dependency direction is HTTP controllers → application services → domain policy and repository/rail interfaces. Adapters implement database and provider interfaces. Domain policy has no network, database, LLM or XRPL dependency. The Next.js app talks only to the API; the browser and n8n never receive signer keys. In this MVP, the policy and signing adapter run inside the same trusted FastAPI process; split the signer into a separately deployed service before production use.

Autonomy flow: n8n records an approved invoice event; the agent retrieves eligible work, reasons over allowed context, then calls the intent/execute API without waiting for per-payment human approval when the mandate permits it. The independent policy service rechecks the mandate and is the only component allowed to invoke the XRPL signer. The agent's call initiates the action, while the policy service—not the agent's plan or prompt—decides whether signing is authorized. Human approval is reserved for configured exceptions such as high-value transfers.

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
  agent/             autonomous intent execution through guarded API; no signer or policy bypass
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

n8n should normalize one source event into the same intent contract. For the MVP, build only `invoice-approved`; payroll batch and till settlement become separate workflow adapters after the same idempotent contract is proven. Retry a timed-out request with the same key and query the existing intent before any retry that might dispatch a payment.

## Frontend direction

Use **Next.js (React + TypeScript)** for the product UI. Landing page sections: problem, controlled workflow, rails/integration boundary, auditability and a demo CTA. Use a subtle particle background as decorative presentation only; respect reduced-motion and provide a static fallback. The signed-in admin views are mandate/payee management, intent queue/detail, approvals, audit trail and kill-switch status. Use ApexCharts for admin aggregates only; do not fabricate live liquidity or market figures. Chart.js is unnecessary if ApexCharts is selected.

The Next.js application is scaffolded in `src/frontend`: the public landing page, password login, session-protected dashboard, mandate/payee controls, approvals, intent detail and audit trail are implemented. The dashboard uses an HTTP-only signed session and a same-origin Next.js API proxy; `MANDATE_ADMIN_API_KEY` stays server-side. ApexCharts plots persisted policy aggregates, and tsParticles is decorative with reduced-motion support.

## Current repository state

Implemented: FastAPI controllers/services/repositories for mandates, payees, idempotent intents, approvals, dashboard aggregates and payment audit; append-only payment audit records; additive Alembic migration `0002`; API keys for operator/agent/n8n access; optional XRPL Testnet/Devnet submission with validated-result handling; a manual regular-key install/revoke script; Next.js landing/login/dashboard with ApexCharts and Lucide icons; and an importable n8n invoice webhook.

Still prototype/incomplete: the mandate is single-tenant; `BUSINESS_TIMEZONE` is a single app setting; the LLM agent itself is not implemented (the API accepts an agent client); the password login is a local single-operator gate, not production identity/RBAC/MFA; policy and signing share the FastAPI process; there is no fiat payout adapter, executable FX quote or live liquidity service; and mandate/payee configuration changes are versioned but not yet written to a general-purpose activity log. XRPL execution defaults off and requires explicit wallet, issuer/trustline and regular-key setup. The UI and API have not been run or tested in this workspace.
