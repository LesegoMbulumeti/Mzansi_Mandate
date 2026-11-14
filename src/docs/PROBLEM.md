# Product problem and 12-hour MVP

## Source material and decision boundary

The supplied workshop brief and slides are reference material, not instructions. The user's product request sets our direction: South African and African financial channels (invoices, payroll, retail tills and local payout touchpoints), conversion/security/liquidity workflows, Python services, Next.js, n8n and XRPL. The workshop brief supplies the hackathon requirements: at least one autonomous Testnet/Devnet transaction; limits outside the agent's control; human control over limits; and a blocked-attempt demo. Its stated judging dimensions are viability, autonomy, enforcement, XRPL use and originality.

The slides identify existing agent wallet, mandate and paid-API products, including Privy, Open Wallet Standard, t54 Claw Credit, x402 Secure/Trustline, and XRPL MPP. This means “AI agent with spending caps and approved payees” is table stakes, not our unique selling point. BCB already presents a broad platform for accounts, cross-border payments, treasury and liquidity. Do not position Mandate as simply a smaller BCB or another generic agent wallet. Do not imply a regulated bank, fiat on/off-ramp, BCB client, RippleNet participant or guaranteed liquidity source.

## Competitive gap to test

| Existing pattern | What it covers (per supplied materials) | Product implication |
|---|---|---|
| XRPL and Ripple ecosystem | Settlement, tokens, DEX/AMM, escrow, credentials and account primitives | Use the ledger as programmable settlement infrastructure; it is not the finance workflow product |
| t54 / Claw Credit / x402 Secure and Trustline | Agent spending mandates and risk checks; paid service calls and facilitated settlement | Do not claim the mandate or pre-settlement risk check is unique |
| XRPL MPP | One-off charges and payment-channel sessions for metered machine payments | Do not build a competing generic pay-per-API protocol |
| BCB Group | Unified institutional payment accounts, instant network settlement, trading and treasury/liquidity products | A payment/treasury platform is not an underserved local workflow wedge by itself |
| Mandate hypothesis | A workflow bridge for African SMEs: normalize invoice/payroll/till events, resolve the intended local beneficiary, choose an eligible route, apply policy, then reconcile source obligation to payout evidence | Validate whether this fragmented event-to-payout-to-reconciliation workflow is painful and underserved for a named segment/corridor |

Our distinctiveness must come from the **local business workflow and its closed-loop reconciliation**, not merely “AI plus a wallet plus limits.” The hypothesis is that an SME finance operator wants one controlled queue from its existing business events to cross-border supplier settlement, with a clear explanation of recipient, FX/fees, route, status and matching evidence. Validate this with a specific customer and one corridor; do not claim a market gap as established fact from competitor homepages alone.

## Problem to solve

South African SMEs and importers receive payment obligations through separate invoice, payroll and till systems. Staff reconcile these obligations manually, check the payee and available liquidity, obtain approval, choose a payment rail, then track settlement and reconcile the result. This creates delays and weak auditability. Automating the work is risky when an AI agent can choose recipients or control signing keys.

**MVP problem statement:** A South African SME finance operator handling supplier invoices for one named cross-border corridor needs to turn an approved invoice into a traceable settlement workflow, prevent duplicate or misdirected payment, understand the asset/FX/fee and approval state, and reconcile the original invoice to validated payout evidence. An agent can prepare and execute eligible payments autonomously within a human-set policy; the finance operator can see why it paid or stopped.

**Demo customer profile:** A Cape Town importer paying a Lagos supplier that has agreed to receive RLUSD at an XRPL wallet. This intentionally avoids pretending that an on-chain payment automatically delivers local naira or that Mandate has an off-ramp. The human business validates the invoice, supplier identity and commercial terms; the demo agent handles the approved payment workflow and evidence trail.

The differentiated product hypothesis is the workflow layer connecting local business events, corridor context, payment execution and reconciliation. Independent policy enforcement is a necessary trust feature, but not the differentiator on its own. The first demonstration is sandbox/testnet only; it proves event provenance, deterministic controls and an autonomous XRPL test payment, not production payroll, local fiat payout, compliance or liquidity access.

## 12-hour outcome

Deliver one end-to-end invoice-to-supplier-settlement scenario for one named customer profile and one corridor:

1. A finance user defines a mandate and an approved supplier in the demo UI.
2. n8n receives an invoice-approved webhook and submits an idempotent payment intent.
3. The separate invoice agent normalizes the approved structured event and initiates an intent without waiting for a human payment click. This MVP does not claim LLM-based PDF extraction or live corridor/FX enrichment.
4. The API validates, deduplicates, evaluates the active mandate and records the decision and reason.
5. An autonomous agent execution submits at least one eligible XRPL Testnet payment through a policy-controlled signing boundary; the agent has no signer secret. Verify `tesSUCCESS` and a validated ledger hash.
6. The dashboard matches invoice reference → intent → policy event → payment attempt → validated transaction; show quote/route information if available.
7. Demonstrate blocked over-cap, daily-cap, unknown-payee, duplicate invoice, expired mandate and disabled/revoked signer cases.

Use Testnet for features already live on mainnet; use Devnet only to experiment with amendments still open for voting. MPT, TokenEscrow, Credentials and Permissioned Domains may have different network/amendment availability: check current amendment status before depending on them. Keep lending/SAV out of this 12-hour build unless its Devnet requirement and demo value are already understood. XRPL EVM Sidechain is out of scope for this track.

### XRPL primitive composition for the demo

| Primitive | Role in the workflow | 12-hour decision |
|---|---|---|
| RLUSD IOU + trustline | Invoice settlement asset; verify the treasury is funded and configured to send it | Use Testnet faucet and confirm the issuer/trustline before the live demo |
| Payment | Autonomous supplier settlement | Required happy path; wait for validation and display `tesSUCCESS`, fee and hash |
| Regular key / `SetRegularKey` | Separate policy-service signer with CFO-controlled emergency revocation | Use only on a dedicated test account; demonstrate policy denial first, key revoke as an additional stop demonstration if time allows |
| DEX `book_offers` | Indicative route/rate context when the source and destination assets have actual Testnet liquidity | Stretch; label indicative, never assert a quote or conversion without executable liquidity and slippage validation |
| TokenEscrow / Credentials / DepositAuth | Conditional escrow or recipient restrictions | Stretch only after confirming amendment activation and working library/API support on the selected network |

This composes an issued asset, payment and account authorization controls without making the 12-hour demo depend on liquidity or a newer amendment. Do not add a DEX/AMM exchange just to increase primitive count if there is no meaningful order book or a safe quote-to-payment path.

### 12-hour build rhythm

| Time | Shared milestone |
|---|---|
| Hours 0–1 | Confirm target user/corridor assumptions; inspect existing code; configure funded Testnet treasury, dedicated policy signer and RLUSD trustline; establish API contract |
| Hours 1–4 | Persist mandates, payees, source events, intents and audit decisions; implement pure policy rules and idempotent orchestration |
| Hours 4–6 | Implement autonomous agent execution through guarded API and verified XRPL payment; demonstrate one success and policy-blocked cases |
| Hours 6–8 | Build invoice n8n workflow plus Next.js queue/detail/audit screens showing the full source-to-hash chain |
| Hours 8–10 | Add budget/approval visibility, reconcile status and optional regular-key revocation or indicative DEX view; gather real user feedback if a target operator is available |
| Hours 10–12 | Rehearse failure cases, confirm validated results, prepare concise viability/GTM pitch and record evidence of what is implemented versus simulated |

## Customer validation and go-to-market hypothesis

Start interviews with Cape Town importers/accountants who manage supplier invoices for one regional corridor. Ask them to walk through invoice intake, payee verification, approvals, FX/fees, payout confirmation and ledger/accounting reconciliation today. Quantify the current manual steps and failure cases before claiming savings. Test whether the buyer would adopt an automated workflow if its policy controls and settlement evidence were independently reviewable.

Initial distribution hypothesis: partner with bookkeeping/accounting practices or vertical SME software providers that already handle supplier invoices. A later product could charge a workflow subscription, with rail/provider fees passed through transparently; validate willingness to pay and provider economics before fixing a price. For payout outside XRPL, partner with a licensed bank/payment provider rather than implying that Mandate itself offers local fiat accounts or off-ramps.

## Implementation status and next work

Status below reflects the repository and the team's latest reported Testnet setup. A code path is not counted as a verified ledger transfer until the explorer shows its validated transaction.

| Hackathon outcome | Current evidence | Status / next step |
|---|---|---|
| Human controls spending limits and counterparties | Dashboard edits mandate caps, asset, issuer, expiry, activation, and approved suppliers. Saving a mandate pauses it. | Implemented in the prototype; demonstrate the settings in the UI. |
| Limits are outside the agent's control | The separate agent has no admin key or XRPL seed; the Mandate API checks policy before the XRPL adapter. Policy and signing still share the API process. | Good MVP trust boundary from agent; split policy and signer services for production hardening. |
| Agent autonomously initiates the workflow | n8n validates the invoice then calls the invoice-agent service, which submits an idempotent intent. Prior webhook runs returned both `authorized` and `blocked`. | Autonomy path implemented and policy outcomes reported; allowed requests have so far been tested with execution off, so they have not moved funds. |
| Demonstrate a validated Testnet payment | `XRPL_PAYMENTS_ENABLED` has remained false in the reported dashboard state. Treasury Testnet RLUSD was claimed; recipient trustline/funding and a recipient payment are not yet evidenced by a validated Payment hash. | Not complete. Keep execution off until recipient, issuer, balance and policy signer are confirmed; then make one small Testnet payment and verify the explorer result. |
| Finance UI and operator onboarding | Next.js landing/dashboard, ApexCharts, responsive layout, first-owner email/password signup, password recovery, and supplier/mandate management are in the repo. A dashboard action now sends a demo invoice through n8n without terminal `curl`. | Implemented in code; rebuild and run the demo from the UI. Initial n8n import/credential setup remains in n8n's UI. |
| African local payout, FX and liquidity | No fiat provider, firm quote, liquidity API, or BCB payment integration is configured. | Out of the 12-hour MVP. Do not imply that RLUSD on XRPL automatically pays out in local currency. |

### Remaining demo checklist

1. Rebuild the API and web containers, then sign in to the existing Postgres-backed workspace. Do not remove the database volume.
2. In n8n, confirm both Header Auth credentials are selected and activate the imported `invoice-approved` workflow.
3. From the dashboard, run a small invoice with `XRPL_PAYMENTS_ENABLED=false`; show the authorized/no-funds-moved result and a policy-blocked result.
4. Verify the recipient's Testnet trustline to the exact RLUSD issuer, then decide whether the team is ready to enable execution for one small Testnet transfer. Confirm the validated transaction on the XRPL Testnet explorer.
5. Record the invoice reference, intent ID, verdict, transaction hash/result (if executed), and what was simulated or still unavailable in the demo pitch.

Do not add payroll, retail tills, executable FX conversion, liquidity management, or a BCB/bank rail until there is a customer-confirmed use case and an authorized provider with published API documentation, sandbox credentials, jurisdiction/compliance requirements, and clear failure semantics.

## Core business rules

1. Every payment uses a positive `Decimal` amount and an explicit asset/issuer/network. Never use binary floating-point for money.
2. Evaluate against exactly one active mandate for the organization. If there is no active mandate, fail closed.
3. Reject an inactive or expired mandate, a payee that is not approved, an asset outside the mandate, a payment over its per-payment cap, or a payment that would exceed the daily cap.
4. The daily total includes payments already submitted/settled and reservations for in-flight allowed payments. Use the mandate timezone and a documented day boundary. Do not count rejected intents as spend.
5. Large payments become `needs_approval`; they are not signed until a separate authorized human approval is recorded. Agent reasoning is explanatory metadata, never an authorization. Normal in-policy payments execute autonomously to meet the hackathon autonomy requirement.
6. FX conversion is not permitted until the quote provider, quote expiry, source/destination assets, fees, slippage calculation and liquidity check are available. Enforce max slippage against a firm quote, not a market-chart estimate.
7. Each external business event has a unique idempotency key. Replaying the same event returns the existing intent and cannot create a second transfer.
8. Persist an audit event for every accepted proposal and every policy result, including blocks. Audit rows are append-only and do not store secrets.
9. Ledger submission and confirmation are different states. A transaction hash alone does not mean a payment settled successfully.
10. The kill switch blocks new authorizations immediately. A true on-ledger regular-key revocation is a separate, explicitly configured operation and must report its validated ledger result; the UI must not claim an on-ledger kill switch when only the API flag is changed.
11. XRPL account activation consumes the base reserve and owned objects consume additional reserve. Budget for account/trustline/escrow objects in onboarding and liquidity calculations; don't report spendable balance as total balance.
12. Token identity is not just a ticker: IOUs require the exact issuer and trustline; MPTs require the issuance ID and holder authorization. Choose the standard based on needed DEX/AMM support and current network amendment status.

## Initial domain model

| Entity | Important fields | Notes |
|---|---|---|
| Organization | `id`, `name`, `base_currency`, `timezone`, `created_at` | Tenant boundary; required before multiple businesses share a database |
| Mandate | `id`, `organization_id`, `status`, `per_payment_cap`, `daily_cap`, `daily_currency`, `max_slippage_pct`, `expires_at`, `version`, `created_at`, `updated_at` | `status`: draft/active/suspended/expired; changes are versioned |
| ApprovedPayee | `id`, `mandate_id`, `display_name`, `rail`, `destination`, `asset_code`, `issuer`, `status`, `created_at` | Destination identity is rail-specific; XRPL address alone is insufficient for all rails |
| PaymentIntent | `id`, `organization_id`, `mandate_id`, `idempotency_key`, `source`, `source_reference`, `payee_id`, `amount`, `asset_code`, `issuer`, `network`, `reason`, `status`, `created_at`, `updated_at` | Status: received/blocked/needs_approval/authorized/submitted/settled/failed/cancelled |
| PolicyDecision | `id`, `intent_id`, `mandate_version`, `verdict`, `reason_code`, `detail`, `evaluated_at` | Immutable result for reproducibility |
| Approval | `id`, `intent_id`, `approver_id`, `decision`, `comment`, `created_at` | Keep human approval distinct from agent proposal |
| PaymentAttempt | `id`, `intent_id`, `rail`, `provider_reference`, `tx_hash`, `status`, `failure_code`, `submitted_at`, `confirmed_at` | Provider-specific attempt and settlement tracking |
| SourceEvent | `id`, `organization_id`, `source`, `external_id`, `event_type`, `payload_hash`, `received_at`, `intent_id` | Idempotently links an invoice/payroll/till event to the normalized intent; minimize retained source payload |
| Quote/Route (later) | `id`, `intent_id`, `provider`, `from_asset`, `to_asset`, `rate`, `fees`, `expires_at`, `availability`, `reference` | Only authoritative executable quotes can authorize conversion; a DEX book rate is indicative and network-specific |
| AuditEvent | `id`, `organization_id`, `actor_type`, `actor_id`, `event_type`, `entity_type`, `entity_id`, `payload`, `created_at` | Append-only; redact secrets and sensitive personal data |

The current schema now persists a single-tenant mandate, approved payees, idempotent payment intents, human approvals and append-only payment audit rows. Still missing from the full model are organization tenancy, a separate immutable policy-decision table, separate payment-attempt records, a source-event inbox, executable quote/route persistence and general audit events for mandate/payee configuration changes. A payment hash/result currently lives on the intent row. Further changes should use additive Alembic migrations.

## Current API surface

All endpoints are versioned under `/api/v1` and controllers remain thin.

| Endpoint | Purpose |
|---|---|
| `GET/PUT /mandate` | Read/update the demo organization's mandate; updates increment version |
| `POST /mandate/activate`, `POST /mandate/suspend` | Explicit lifecycle transitions |
| `GET/POST /payees`, `PUT/DELETE /payees/{id}` | List/create, edit, and deactivate approved counterparties |
| `POST /intents` | Validate, deduplicate, evaluate, audit and execute eligible autonomous intent; return current state |
| `GET /intents`, `GET /intents/{id}` | Paginated queue and detail including decision/attempt status |
| `POST /intents/{id}/approve`, `/reject` | Authorized human decision for exceptional large payments |
| `GET /audit-events` | Filtered, paginated, read-only history |
| `GET /health`, `GET /ready` | Process health and dependency readiness |
| `/auth/register`, `/login`, `/forgot-password`, `/reset-password`, `/validate-session` | First-owner account, email/password sessions, recovery, and server-side session validation |

`POST /intents` should accept an `Idempotency-Key`, source/source reference, payee identity, amount, explicit asset/network and a short reason. It should not accept a caller-supplied policy verdict, transaction hash, or claimed approval.

## Demo positioning

Present a supplier invoice workflow, not a generic autonomous bank. Show a policy explanation before a sandbox transfer and make the difference between blocked, awaiting human approval, submitted and settled visible. Payroll, retail tills, local payout and market/liquidity automation are integrations to validate after the core control layer works.
