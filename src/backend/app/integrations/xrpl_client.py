"""XRPL adapter. Only the Policy Service side should import this with a signer seed."""
from decimal import Decimal

from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.asyncio.transaction import submit_and_wait
from xrpl.models.transactions import Payment, SetRegularKey
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.utils import xrp_to_drops
from xrpl.wallet import Wallet

from app.config import settings


class XrplClient:
    async def pay(self, payee: str, amount: Decimal, currency: str, issuer: str | None = None) -> str:
        signer = Wallet.from_seed(settings.policy_signer_seed)
        if currency == "XRP":
            value = xrp_to_drops(amount)
        else:
            value = IssuedCurrencyAmount(currency=currency, issuer=issuer, value=str(amount))
        tx = Payment(account=settings.treasury_address, destination=payee, amount=value)
        async with AsyncWebsocketClient(settings.xrpl_ws_url) as client:
            # Regular-key signing: treasury master key stays offline with the CFO.
            res = await submit_and_wait(tx, client, signer, check_fee=True)
        return res.result["hash"]

    async def revoke_signer(self, cfo_wallet: Wallet) -> str:
        """Kill switch on the ledger: clears the regular key so the policy signer can no longer sign."""
        tx = SetRegularKey(account=settings.treasury_address)
        async with AsyncWebsocketClient(settings.xrpl_ws_url) as client:
            res = await submit_and_wait(tx, client, cfo_wallet)
        return res.result["hash"]
