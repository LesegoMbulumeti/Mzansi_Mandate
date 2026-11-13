# Mandate

**African SME payables from business event to verified settlement.**

An agent executes eligible supplier payments from approved invoice events, while an independent policy boundary controls signing and the finance team can reconcile each payout back to its source obligation. Spending limits alone are not the differentiator; local workflow integration and payout evidence are the product hypothesis.

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

**The agent never holds the treasury key.** It autonomously initiates eligible payment intents. An independent Policy Service checks the mandate and is the only thing that can sign, using a dedicated regular key. A human sets limits outside the agent; the offline master key can revoke the regular key on-ledger as an emergency stop. The policy service enforces per-payment limits; key revocation does not.

```
Payroll / Invoices / Tills --> n8n --> Intent API --> Agent --> Policy Service --> XRPL
                                           event          executes     enforces + signs Testnet/Devnet
                                                                           ^
                                              React dashboard (CFO sets mandate, kill switch)
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
  agent/          LLM agent: initiates eligible intents, never signs
backend/migrations/   Alembic versions
frontend/             Next.js landing page and finance dashboard
n8n/                  exported workflows
docs/                 PROBLEM.md, ARCHITECTURE.md, SETUP.md
```

## Quick start

```bash
cp .env.example .env
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload     # http://localhost:8000/docs
PYTHONPATH=. pytest -q
```

Everything in containers (API, Postgres, n8n):

```bash
docker compose up --build
```

Frontend (once scaffolded):

```bash
cd frontend && npm install && npm run dev   # Next.js default: http://localhost:3000
```

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

Testnet only. Never commit seeds or `.env`. The agent process must never read `POLICY_SIGNER_SEED`.
