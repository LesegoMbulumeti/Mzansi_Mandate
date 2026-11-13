# Architecture

Clean MVC with a strict dependency direction: controllers -> services -> repositories / integrations. Models and schemas sit at the edges.

```
backend/app/
  main.py                 FastAPI app factory, router wiring
  config.py               Settings from env (pydantic-settings)
  controllers/            HTTP only: parse, call service, return schema
  services/               Business logic: policy engine, payment orchestration, audit
  repositories/           Persistence (SQLite/SQLAlchemy or in-memory for MVP)
  models/                 Domain entities (Mandate, PaymentIntent, AuditEntry)
  schemas/                Pydantic request/response contracts
  integrations/
    xrpl_client.py        XRPL Testnet: sign, submit, rates, revoke key
    rails/                Pluggable payment rails (xrpl now; BCB/fiat adapters later)
  agent/                  LLM agent: proposes intents, never signs
```

## Trust boundaries

1. **Agent** (untrusted): reads context, proposes intents over the API. No keys.
2. **Policy Service** (trusted, separate process in production): evaluates the mandate, signs with the treasury regular key.
3. **XRPL** (ultimate enforcer): CFO can `SetRegularKey` to clear the Policy Service's authority; DepositAuth/Credentials restrict who can receive; Escrow holds large payments.
4. **CFO** (human): changes mandate via authenticated dashboard; master key kept offline.

## Policy checks (in order)

mandate active and not expired -> payee approved -> amount <= per-payment cap -> daily total + amount <= daily cap -> FX slippage within limit -> large payment routed to escrow / second signer.

Every verdict, allowed or blocked, is written to the audit log with the agent's stated reason.

## Integrations

| Source | Purpose | API |
|---|---|---|
| XRPL Testnet | Settlement | `wss://s.altnet.rippletest.net:51233` via `xrpl-py` |
| XRPL DEX | FX / market rate | `book_offers` |
| tryrlusd.com | Test RLUSD | faucet |
| n8n | Business events in | Webhook -> `POST /api/v1/intents` |
| Future rails | Fiat on/off ramp | `rails/` adapter (BCB-style accounts) |
