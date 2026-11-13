# n8n invoice workflow

Import `invoice-approved.json` into n8n. The webhook normalizes an invoice event and calls the same idempotent FastAPI intent endpoint used by an agent. It does not send a private key or bypass policy checks.

## Configure the shared credential

1. Create a **Header Auth** credential named `Mandate invoice webhook` with header `X-Invoice-Webhook-Secret` and value `N8N_INBOUND_WEBHOOK_SECRET` from `.env`. Select it on the trigger node.
2. Create a second **Header Auth** credential named `Mandate API shared secret` with header `X-Webhook-Secret` and value `N8N_SHARED_SECRET` from `.env`. Select it on the `Submit payment intent` node.
3. Activate the workflow. The inbound endpoint is `POST http://localhost:5678/webhook/invoice-approved`; callers must send `X-Invoice-Webhook-Secret`.

The API's Docker service name is `api`, so the workflow posts to `http://api:8000/api/v1/intents`. The workflow maps `invoice_id` to a stable idempotency key; retries of one invoice cannot produce a second payment intent.

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

Replace the example destination and issuer with the exact approved Testnet accounts configured in the dashboard. An event for an unapproved payee, inactive mandate, mismatched asset, expired budget or over-budget amount is recorded and blocked by the API. With XRPL execution disabled, an allowed event is recorded as `authorized` and explicitly reports that no funds moved.
