# n8n invoice workflow

Import `invoice-approved.json` into n8n. The workflow authenticates the source invoice event, normalizes it, and calls the standalone invoice-agent service. The agent independently submits an idempotent intent to the Mandate API. The API rechecks policy before it can call the XRPL adapter. The agent container receives no database URL, treasury seed, or policy signer seed.

## Configure the shared credential

1. Create a **Header Auth** credential named `Mandate invoice webhook` with header `X-Invoice-Webhook-Secret` and value `N8N_INBOUND_WEBHOOK_SECRET` from `.env`. Select it on the trigger node.
2. Create a second **Header Auth** credential named `Mandate invoice agent` with header `X-Agent-API-Key` and value `AGENT_API_KEY` from `.env`. Select it on the `Submit payment intent` node.
3. Activate the workflow. The inbound endpoint is `POST http://localhost:5678/webhook/invoice-approved`; callers must send `X-Invoice-Webhook-Secret`. In Docker, the agent is reachable to other containers as `http://agent:8100`; local development can reach it at `http://localhost:8100`.

After activation and credential selection, use the signed-in dashboard's **Try the invoice workflow** panel for routine demo requests. The web server forwards a sample invoice to n8n with the inbound secret stored server-side; no terminal `curl` request or browser-side secret is needed. The panel is disabled while XRPL execution is enabled. For first-time n8n setup, import this workflow, configure both credentials, then activate it in n8n.

The agent's Docker service name is `agent`, so the workflow posts to `http://agent:8100/api/v1/agent/invoices`. The agent derives a stable idempotency key from `invoice_id` before calling the API; webhook retries cannot create a second payment intent.

## Sample webhook body

```json
{
  "invoice_id": "INV-2048",
  "supplier_name": "Atlas Components",
  "payee": "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe",
  "amount": "2450.00",
  "currency": "RLUSD",
  "issuer": "rRLUSDIssuerAddressFromTestnet",
  "network": "testnet",
  "reason": "Approved supplier invoice INV-2048"
}
```

Replace the example destination and issuer with the exact approved Testnet accounts configured in the dashboard. An event for an unapproved payee, inactive mandate, mismatched asset, expired mandate or over-budget amount is recorded and blocked by the API. With XRPL execution disabled, an allowed event is recorded as `authorized` and explicitly reports that no funds moved. This MVP agent operates on structured invoice events; it does not use an LLM to read invoice PDFs or make credit/FX judgments.
