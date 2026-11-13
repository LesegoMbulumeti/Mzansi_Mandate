# Mandate

**CFO-grade rails for AI agents that move money on the XRP Ledger.**

Built by team **Mzansi Mandate** for the Node Engine Hackathon 2026, Ripple Agentic Finance track.
Challenge: *"Would your CFO sign off?"*

An AI agent can pay, convert and reconcile, but no finance lead will let it near the treasury until four questions are answered:

| CFO question | Mandate answer |
|---|---|
| What is the agent allowed to do? | A **mandate**: per-payment cap, daily budget, FX slippage limit, expiry |
| Who can it pay? | Approved-counterparty allowlist (on-ledger Credentials / DepositAuth where possible) |
| How do I stop it? | Kill switch that revokes the agent's signing authority **on the ledger** |
| How do I prove what it did and why? | Append-only audit log: intent, reasoning, policy decision, XRPL tx hash |

## The one design rule

**The agent never holds the treasury key.** It only *proposes* payment intents. An independent Policy Service checks the mandate and is the only thing that can sign, using the treasury account's regular key. A human sets limits in the dashboard and can revoke that key on-chain.

```
Payroll / Invoices / Tills --> n8n --> Intent API --> Agent (LLM) --> Policy Service --> XRPL
                                                      proposes        enforces + signs   Testnet/Devnet
                                                                           ^
                                              React dashboard (CFO sets mandate, kill switch)
```

## Target customer

South African importers paying suppliers in Lagos and Nairobi, where each cross-border payment loses days and FX margin. The finance owner approves a mandate once; the agent runs supplier payables inside it.

## Stack

| Layer | Tech |
|---|---|
| API | Python 3.12, **FastAPI**, Pydantic v2, clean MVC |
| Data | **SQLAlchemy 2.0**, **Alembic** migrations, SQLite (dev) / Postgres 16 (Docker) |
| Ledger | `xrpl-py`, XRPL Testnet (Devnet for Lending/Vault), test RLUSD |
| Frontend | React + Vite |
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
  agent/          LLM agent: proposes intents, never signs
backend/migrations/   Alembic versions
frontend/             React dashboard
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

Frontend:

```bash
cd frontend && npm install && npm run dev   # http://localhost:5173
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

- [Problem scope and 12-hour plan](docs/PROBLEM.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Setup, GitHub workflow and migrations](docs/SETUP.md)

## Security

Testnet only. Never commit seeds or `.env`. The agent process must never read `POLICY_SIGNER_SEED`.
