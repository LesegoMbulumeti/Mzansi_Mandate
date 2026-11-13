"""Invoice agent: normalize an approved invoice and autonomously request an intent.

This process has no database or XRPL signer credentials. Financial authority remains
at the Mandate API, which re-evaluates every intent against the active mandate.
"""
import hashlib

import httpx

from app.agent.schemas import InvoiceEvent


class InvoiceAgent:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key

    async def process(self, invoice: InvoiceEvent) -> tuple[int, dict]:
        # Stable across webhook retries while avoiding exposing arbitrary source IDs
        # in an HTTP header or exceeding the API's idempotency-key limit.
        digest = hashlib.sha256(invoice.invoice_id.encode("utf-8")).hexdigest()
        payload = {
            "payee": invoice.payee,
            "amount": str(invoice.amount),
            "currency": invoice.currency,
            "issuer": invoice.issuer,
            "network": invoice.network,
            "reason": f"Autonomous invoice agent: {invoice.reason}",
            "source": "invoice",
            "source_reference": invoice.invoice_id,
        }
        headers = {
            "X-Agent-API-Key": self.api_key,
            "Idempotency-Key": f"invoice:{digest}",
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.api_url}/api/v1/intents", json=payload, headers=headers
                )
        except httpx.TimeoutException:
            # The caller can retry the same invoice; API idempotency prevents a
            # second payment if the first request already reached the ledger.
            return 504, {
                "detail": "Mandate API timed out; retry this invoice with the same invoice_id",
                "invoice_id": invoice.invoice_id,
                "retryable": True,
            }
        except httpx.HTTPError:
            return 502, {"detail": "Mandate API is unavailable", "retryable": True}

        try:
            body = response.json()
        except ValueError:
            body = {"detail": "Mandate API returned an invalid response"}
        return response.status_code, body
