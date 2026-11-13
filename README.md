# Mandate

**African SME payables from business event to verified settlement.**

An autonomous invoice-agent service receives structured, approved supplier invoice events, submits payment intents, and leaves payment authority with the Mandate API's independent policy checks. The finance team can reconcile each payout back to its source obligation. Spending limits alone are not the differentiator; local workflow integration and payout evidence are the product hypothesis. The current agent is event-driven and deterministic; LLM-based PDF extraction is not implemented.

Built by team **Mzansi Mandate** for the Node Engine Hackathon 2026, Ripple Agentic Finance track.
Challenge: *"Would your CFO sign off?"*

An agent can initiate a payment, but a finance team needs four answers before trusting that workflow:

| CFO question | Mandate answer |
|---|---|
| What is the agent allowed to do? | A **mandate**: per-payment cap, daily budget, FX slippage limit, expiry |
| Who can it pay? | Approved-counterparty list, verified against the invoice and payment destination |
| How do I stop it? | Policy kill switch plus optional emergency regular-key revocation on XRPL |
| How do I prove what it did and why? | Source invoice → intent → policy decision → payment result, including validated ledger evidence |

## The one design rule

**The agent never holds the treasury key.** It autonomously initiates eligible payment intents. The separate Mandate API checks the human-defined mandate and is the only service that can reach the XRPL signer. A human sets limits outside the agent; the offline master key can revoke the regular key on-ledger as an emergency stop. The API policy enforces per-payment limits; key revocation does not.

```
Approved invoice --> n8n --> Invoice Agent service --> Mandate API policy --> XRPL Testnet/Devnet
                                                        checks + signs
                           React dashboard (CFO sets mandate, kill switch) ───┘
```

## Target customer

Initial demo profile: a Cape Town importer paying a Lagos supplier who agrees to receive RLUSD to an XRPL wallet. The first release demonstrates invoice-to-ledger reconciliation on Testnet; it does not claim to deliver local naira or provide an off-ramp. Validate the workflow with a real importer before making broader market claims.

## Stack

| Layer | Tech |
|---|---|
| API | Python 3.12, **FastAPI**, Pydantic v2, clean MVC |
| Data | **SQLAlchemy 2.0**, **Alembic** migrations, SQLite (dev) / Postgres 16 (Docker) |
| Ledger | `xrpl-py`, XRPL Testnet (Devnet for Lending/Vault), test RLUSD |
| Frontend | Next.js (React + TypeScript) |
| Automation | n8n |
| CI | GitHub Actions (ruff, migrations, pytest) |

## Project layout

```
backend/app/
  controllers/    HTTP layer only
  services/       policy engine, payment orchestration, audit
  repositories/   persistence
  models/         domain dataclasses (domain.py) and SQLAlchemy tables (orm.py)
  schemas/        Pydantic request/response contracts
  integrations/   xrpl_client.py, rails/ (pluggable payment rails)
  agent/          separate event-driven invoice agent; initiates intents, never signs
backend/migrations/   Alembic versions
frontend/             Next.js landing page and finance dashboard
n8n/                  exported workflows
docs/                 PROBLEM.md, ARCHITECTURE.md, SETUP.md
```

## Quick start

Run from `src/`. Copy `.env.example` to `.env` and change `ADMIN_LOGIN_PASSWORD` and `SESSION_SECRET` before starting. Payment execution is disabled by default.

```bash
cp .env.example .env
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload     # http://localhost:8000/docs
PYTHONPATH=. pytest -q
```

Everything in containers (API, separate invoice agent, Postgres, Next.js, n8n):

```bash
docker compose up --build
```

Frontend:

```bash
cd frontend && npm install && npm run dev   # Next.js default: http://localhost:3000
```

Dashboard password: `ADMIN_LOGIN_PASSWORD` from `.env`. The Next.js server proxies admin requests with the server-side `ADMIN_API_KEY`; it does not expose this key to browser code. API docs are at `http://localhost:8000/docs`, n8n at `http://localhost:5678`.

## First run

1. Open `http://localhost:3000`, then sign in with `ADMIN_LOGIN_PASSWORD`.
2. Set up a mandate with an expiry, asset and issuer; add the supplier's XRPL destination; activate the mandate.
3. Import `n8n/invoice-approved.json` and add the Header Auth credentials described in `n8n/README.md`.
4. Post an invoice event to the n8n webhook. n8n calls the separate invoice-agent service, which autonomously submits the intent to the Mandate API. With `XRPL_PAYMENTS_ENABLED=false`, an allowed intent is recorded as authorized and the UI clearly states that no funds moved.

### Optional XRPL Testnet execution

Keep execution disabled until a dedicated treasury account and receiver are funded/configured on Testnet. Install a separate policy regular key using the treasury master wallet interactively:

```bash
cd backend
PYTHONPATH=. python scripts/configure_testnet_regular_key.py install
```

The script prompts for the master seed without saving it. Verify it reports validated `tesSUCCESS`. Configure `TREASURY_ADDRESS`, `POLICY_SIGNER_SEED`, `RLUSD_ISSUER`, and `XRPL_PAYMENTS_ENABLED=true` in `.env`, then restart the API. The treasury and receiving account must be able to hold the exact issued asset (RLUSD trustline/issuer). To revoke the policy regular key, run the script with `revoke`; this is an emergency ledger-level stop, distinct from suspending the API mandate.

The API rejects mainnet URLs. The UI does not provide a fiat account, naira payout, market quote or liquidity service.

### Test funds
- Test XRP: https://xrpl.org/resources/dev-tools/xrp-faucets
- Test RLUSD: https://tryrlusd.com
- Explorer: https://testnet.xrpl.org

## Database migrations

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic downgrade -1
```

## Docs

- [Problem scope, domain model and 12-hour plan](docs/PROBLEM.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Setup, GitHub workflow and migrations](docs/SETUP.md)

## Security

XRPL signing is disabled until `XRPL_PAYMENTS_ENABLED=true`. Before enabling it, configure a dedicated Testnet treasury, matching issued-asset issuer/trustline and policy regular key. Never commit seeds or `.env`; the agent and n8n must never receive `POLICY_SIGNER_SEED`.
