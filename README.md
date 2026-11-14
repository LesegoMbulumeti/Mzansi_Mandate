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

Run the full local stack from `src/`. Copy `.env.example` to `.env`, set unique local API secrets and a random `SESSION_SECRET` (at least 32 characters). Keep XRPL execution disabled. This is the only routine start command; database migrations run when the API container starts.

```bash
cd src
cp .env.example .env
docker compose up -d --build
```

Open the product at `http://localhost:3000` and n8n at `http://localhost:5678`. Docker Desktop can show service status and logs. The API documentation at `http://localhost:8000/docs` is for developers; routine demo requests can be sent from the signed-in dashboard. Existing database data is retained by the Compose volume; do not use `docker compose down -v`.

User sign-in is email/password. `ADMIN_API_KEY`, `AGENT_API_KEY`, and webhook secrets are service credentials and must never be entered in the browser or user login form.

## First run

1. Open `http://localhost:3000/register` and create the first owner account. This local prototype has one owner account for a shared workspace; existing mandate and payment data remains in the same database.
2. Set up a mandate with an expiry, asset and issuer; add the supplier's XRPL destination; activate the mandate.
3. Import `n8n/invoice-approved.json` and add the Header Auth credentials described in `n8n/README.md`.
4. Activate the n8n workflow. From the dashboard's **Try the invoice workflow** panel, choose an approved supplier and send a small demo invoice through n8n. The UI shows the intent and policy result. With `XRPL_PAYMENTS_ENABLED=false`, an allowed intent is recorded as authorized and no funds move. This replaces the routine `curl` request; the initial n8n import and credential selection still happen once in n8n's UI.

### Optional XRPL Testnet execution

Keep execution disabled until a dedicated treasury account and receiver are funded/configured on Testnet. Install a separate policy regular key using the treasury master wallet interactively:

```bash
cd backend
PYTHONPATH=. python scripts/configure_testnet_regular_key.py install
```

The script prompts for the master seed without saving it. Verify it reports validated `tesSUCCESS`. Configure `TREASURY_ADDRESS`, `POLICY_SIGNER_SEED`, `RLUSD_ISSUER`, and `XRPL_PAYMENTS_ENABLED=true` in `.env`, then restart the API. The treasury and receiving account must be able to hold the exact issued asset (RLUSD trustline/issuer). To revoke the policy regular key, run the script with `revoke`; this sensitive wallet operation intentionally remains a deliberate command-line task, distinct from routine dashboard actions.

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
