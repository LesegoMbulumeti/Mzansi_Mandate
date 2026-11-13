"""Install/revoke the policy regular key on a dedicated XRPL test account.

Run from backend/ after installing requirements and setting .env:
    PYTHONPATH=. python scripts/configure_testnet_regular_key.py install
    PYTHONPATH=. python scripts/configure_testnet_regular_key.py revoke

The treasury master seed is requested interactively and is never saved by this script.
"""
import argparse
import asyncio
from getpass import getpass

from xrpl.wallet import Wallet

from app.config import settings
from app.integrations.xrpl_client import XrplClient


async def main(operation: str) -> None:
    if not settings.treasury_address:
        raise SystemExit("Set TREASURY_ADDRESS in .env first")
    if not settings.policy_signer_seed and operation == "install":
        raise SystemExit("Set POLICY_SIGNER_SEED in .env first")
    wallet_seed = getpass("Treasury master seed (not stored): ")
    try:
        treasury_wallet = Wallet.from_seed(wallet_seed)
    except Exception as exc:
        raise SystemExit("Could not read a valid XRPL wallet seed") from exc

    result = await XrplClient().configure_regular_key(
        treasury_wallet,
        revoke=(operation == "revoke"),
    )
    print(f"Validated: {result['validated']}")
    print(f"Result: {result['ledger_result']}")
    print(f"Transaction: {result['hash']}")
    if not result["validated"] or result["ledger_result"] != "tesSUCCESS":
        raise SystemExit("Key change did not succeed; inspect the XRPL result before continuing")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("install", "revoke"))
    args = parser.parse_args()
    asyncio.run(main(args.operation))
