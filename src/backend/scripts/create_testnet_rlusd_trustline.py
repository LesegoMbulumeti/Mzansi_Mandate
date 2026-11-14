"""Create the RLUSD Testnet trustline for the configured treasury.

Run from src/backend/ after configuring TREASURY_ADDRESS and RLUSD_ISSUER in
src/.env. The treasury master seed is requested interactively and is never
written to disk or printed.

    PYTHONPATH=. python3 scripts/create_testnet_rlusd_trustline.py
"""
import asyncio
from getpass import getpass

from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.asyncio.transaction import submit_and_wait
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.transactions import TrustSet
from xrpl.wallet import Wallet

from app.config import settings


TESTNET_RLUSD_ISSUER = "rQhWct2fv4Vc4KRjRgMrxa8xPN9Zx9iLKV"
RLUSD_CURRENCY_HEX = "524C555344000000000000000000000000000000"
# The TryRLUSD Testnet faucet only advances to its Claim step when this line's
# limit is at least 100,000 RLUSD. This is a limit, not a token balance.
TRUST_LIMIT = "100000"


async def main() -> None:
    if settings.xrpl_network != "testnet":
        raise SystemExit("This helper is restricted to XRPL Testnet")
    if "s.altnet.rippletest.net:51233" not in settings.xrpl_ws_url:
        raise SystemExit("XRPL_WS_URL must be the XRPL Testnet websocket endpoint")
    if settings.xrpl_payments_enabled:
        raise SystemExit("Keep XRPL_PAYMENTS_ENABLED=false while setting up the trustline")
    if not settings.treasury_address:
        raise SystemExit("Set TREASURY_ADDRESS in src/.env first")
    if settings.rlusd_issuer != TESTNET_RLUSD_ISSUER:
        raise SystemExit("Set RLUSD_ISSUER to Ripple's XRPL Testnet RLUSD issuer in src/.env")

    seed = getpass("Treasury master seed (not stored): ")
    try:
        treasury = Wallet.from_seed(seed)
    except Exception as exc:
        raise SystemExit("That is not a valid XRPL wallet seed") from exc

    if treasury.address != settings.treasury_address:
        raise SystemExit("This seed does not match TREASURY_ADDRESS; no transaction was sent")

    tx = TrustSet(
        account=treasury.address,
        limit_amount=IssuedCurrencyAmount(
            currency=RLUSD_CURRENCY_HEX,
            issuer=TESTNET_RLUSD_ISSUER,
            value=TRUST_LIMIT,
        ),
    )

    async with AsyncWebsocketClient(settings.xrpl_ws_url) as client:
        response = await submit_and_wait(tx, client, treasury, check_fee=True)

    result = response.result
    meta = result.get("meta") or {}
    ledger_result = meta.get("TransactionResult") if isinstance(meta, dict) else None
    validated = bool(result.get("validated"))
    print(f"Validated: {validated}")
    print(f"Result: {ledger_result}")
    print(f"Transaction: {result.get('hash')}")
    if not validated or ledger_result != "tesSUCCESS":
        raise SystemExit("Trustline was not confirmed successful; inspect the Testnet result")


if __name__ == "__main__":
    asyncio.run(main())
