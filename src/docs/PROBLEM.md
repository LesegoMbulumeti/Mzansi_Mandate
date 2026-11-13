# Problem scope: 12-hour plan

## Positioning vs Ripple and BCB

- **Ripple / XRPL**: institutional cross-border rails (RippleNet, RLUSD, custody). Strong settlement layer, but no product that lets a small finance team *safely delegate* to an agent.
- **BCB Group**: regulated e-money accounts, virtual IBANs, BLINC 24/7 fiat settlement, treasury and on/off-ramp. Built for EU/UK institutions and crypto firms; no agent mandate layer and no African retail touch points (tills, payroll runs, stokvels).
- **Gap Mandate fills**: the *control layer* between business events (payroll, invoices, till takings) and the ledger, sized for SMEs and savings groups, with limits enforced outside the agent.

## Problem statement (the one we pitch)

> A Cape Town importer pays Lagos suppliers by bank wire: 2-4 days, 3-5% all-in FX cost, manual approvals in email. Agents could automate it, but the finance owner will not hand over keys. Mandate lets the owner define limits once; an agent pays approved suppliers in RLUSD within those limits, and every action is provable.

## MVP checklist (maps to the judging rubric)

| Requirement | Our implementation | Status |
|---|---|---|
| Autonomous agent tx on Testnet | Agent turns an approved invoice intent into an RLUSD/XRP Payment | [ ] |
| Limits enforced outside the agent | Policy Service holds the regular key; agent has none | [ ] |
| Human sets/changes limits | React mandate editor + kill switch (SetRegularKey revoke) | [ ] |
| Blocked-agent demo | Over-cap, non-approved payee, expired mandate, kill switch | [ ] |
| Viability / GTM | Named customer, switching story, channel (accountants, trade bodies) | [ ] |
| Combine XRPL primitives | Payment + RLUSD + DEX rate + Credentials/DepositAuth + Escrow for large payments | [ ] |

## 12-hour timeline (two people)

| Hours | Person A (backend / XRPL) | Person B (frontend / n8n) |
|---|---|---|
| 0-1 | Repo, env, fund treasury + agent + supplier wallets, RLUSD trustlines | Vite app, n8n up, wireframes |
| 1-4 | Policy engine + mandate model + `/intents` + XRPL payment service | Mandate editor, intent feed, kill switch UI |
| 4-6 | Agent loop (LLM proposes, calls `/intents`), audit log | n8n flows: invoice-approved webhook, payroll batch, till settlement |
| 6-8 | Escrow for large payments, FX rate via DEX `book_offers` | Audit trail page with explorer links, blocked-attempt view |
| 8-10 | Revoke key on-ledger, tests for every block reason | Demo script data, polish |
| 10-12 | Rehearse demo, record video | Pitch deck: pain, customer, GTM, why not BCB/Ripple alone |

## Scope cuts (do only if time remains)

Payroll batches, retail till sweeps, stokvel mode, x402 paid FX-quote service, Lending Protocol. Do not start these before the MVP checklist is green.

## Demo script (3 minutes)

1. CFO sets mandate: R/USD 5,000 per payment, 12,000 per day, two approved suppliers.
2. Invoice arrives via n8n. Agent pays 3,000 to Supplier A. Tx hash on testnet explorer.
3. Agent tries 9,000: **blocked** (per-payment cap). Tries unknown payee: **blocked**.
4. CFO hits kill switch. Agent tries again: **blocked on the ledger**, not just in our app.
5. Audit page shows every attempt with reasoning and policy verdict.
