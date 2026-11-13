"""XRPL adapter. Only the Policy Service side should import this with a signer seed."""
from decimal import Decimal

from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.asyncio.transaction import submit_and_wait
from xrpl.models.transactions import Payment, SetRegularKey
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.utils import xrp_to_drops
from xrpl.wallet import Wallet

from app.config import settings
from app.services.errors import IntegrationError


class XrplClient:
    async def pay(
        self, payee: str, amount: Decimal, currency: str,
        issuer: str | None = None, network: str = "testnet",
    ) -> dict[str, str | bool | None]:
        settings.validate_payment_config()
        if not settings.xrpl_payments_enabled:
            raise IntegrationError("XRPL payment execution is disabled")
        if network != settings.xrpl_network:
            raise IntegrationError("Intent network does not match the configured XRPL network")
        if currency.upper() == "XRP":
            value = xrp_to_drops(amount)
        else:
            if not issuer:
                raise IntegrationError("An issuer address is required for XRPL issued assets")
            try:
                value = IssuedCurrencyAmount(currency=currency, issuer=issuer, value=str(amount))
            except Exception as exc:
                raise IntegrationError("Issued asset configuration is invalid") from exc
        try:
            signer = Wallet.from_seed(settings.policy_signer_seed)
        except Exception as exc:
            raise IntegrationError("Configured XRPL policy signer seed is invalid") from exc
        try:
            tx = Payment(account=settings.treasury_address, destination=payee, amount=value)
        except Exception as exc:
            raise IntegrationError("XRPL payment transaction fields are invalid") from exc
        try:
            async with AsyncWebsocketClient(settings.xrpl_ws_url) as client:
                # Regular-key signing: treasury master key stays offline with the CFO.
                res = await submit_and_wait(tx, client, signer, check_fee=True)
        except Exception as exc:
            # The ledger may have received the transaction even if the client timed out.
            raise IntegrationError(
                "XRPL submission outcome is unknown; reconcile before retrying",
                outcome_unknown=True,
            ) from exc
        result = res.result
        meta = result.get("meta") or {}
        return {
            "hash": result.get("hash"),
            "ledger_result": meta.get("TransactionResult") if isinstance(meta, dict) else None,
            "validated": bool(result.get("validated")),
        }

    async def revoke_signer(self, cfo_wallet: Wallet) -> str:
        """Kill switch on the ledger: clears the regular key so the policy signer can no longer sign."""
        tx = SetRegularKey(account=settings.treasury_address)
        async with AsyncWebsocketClient(settings.xrpl_ws_url) as client:
            res = await submit_and_wait(tx, client, cfo_wallet)
        return res.result["hash"]

    async def configure_regular_key(self, cfo_wallet: Wallet, revoke: bool = False) -> dict:
        """Install or revoke the policy regular key using the offline treasury master wallet."""
        if settings.xrpl_network == "testnet" and "altnet.rippletest.net" not in settings.xrpl_ws_url:
            raise IntegrationError("Testnet key setup requires the XRPL Testnet websocket endpoint")
        if settings.xrpl_network == "devnet" and "devnet" not in settings.xrpl_ws_url:
            raise IntegrationError("Devnet key setup requires the XRPL Devnet websocket endpoint")
        if cfo_wallet.address != settings.treasury_address:
            raise IntegrationError("Treasury master wallet does not match TREASURY_ADDRESS")
        regular_key = None
        if not revoke:
            try:
                policy_wallet = Wallet.from_seed(settings.policy_signer_seed)
            except Exception as exc:
                raise IntegrationError("Configured policy signer seed is invalid") from exc
            if policy_wallet.address == cfo_wallet.address:
                raise IntegrationError("Policy signer must be a separate wallet from the treasury master")
            regular_key = policy_wallet.address
        tx = SetRegularKey(account=settings.treasury_address, regular_key=regular_key)
        async with AsyncWebsocketClient(settings.xrpl_ws_url) as client:
            response = await submit_and_wait(tx, client, cfo_wallet, check_fee=True)
        result = response.result
        meta = result.get("meta") or {}
        return {
            "hash": result.get("hash"),
            "ledger_result": meta.get("TransactionResult") if isinstance(meta, dict) else None,
            "validated": bool(result.get("validated")),
        }
