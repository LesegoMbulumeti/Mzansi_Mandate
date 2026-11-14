from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
if not _ENV_FILE.exists():
    _ENV_FILE = Path.cwd() / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///./mandate.db"
    xrpl_ws_url: str = "wss://s.altnet.rippletest.net:51233"
    xrpl_network: Literal["testnet", "devnet"] = "testnet"
    xrpl_payments_enabled: bool = False
    treasury_address: str = ""
    policy_signer_seed: str = ""
    rlusd_issuer: str = ""
    cors_origins: str = "http://localhost:3000"
    business_timezone: str = "Africa/Johannesburg"
    admin_api_key: str = "local-admin-change-me"
    agent_api_key: str = "local-agent-change-me"
    n8n_shared_secret: str = "local-n8n-change-me"
    app_public_url: str = "http://localhost:3000"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def validate_payment_config(self) -> None:
        """Reject accidental mainnet use; XRPL execution is an explicit opt-in."""
        if not self.xrpl_payments_enabled:
            return
        if not self.treasury_address or not self.policy_signer_seed:
            raise ValueError("XRPL payments require TREASURY_ADDRESS and POLICY_SIGNER_SEED")
        if self.xrpl_network == "testnet" and "altnet.rippletest.net" not in self.xrpl_ws_url:
            raise ValueError("Testnet payments require the XRPL Testnet websocket endpoint")
        if self.xrpl_network == "devnet" and "devnet" not in self.xrpl_ws_url:
            raise ValueError("Devnet payments require the XRPL Devnet websocket endpoint")

    def validate_security_config(self) -> None:
        if self.app_env == "production":
            secrets_to_check = (self.admin_api_key, self.agent_api_key, self.n8n_shared_secret)
            if any(len(secret) < 32 or secret.startswith("local-") for secret in secrets_to_check):
                raise ValueError("Production requires unique API secrets of at least 32 characters")
            if not self.smtp_host or not self.smtp_from_email:
                raise ValueError("Production requires SMTP_HOST and SMTP_FROM_EMAIL for account recovery")

    def validate_business_timezone(self) -> None:
        try:
            ZoneInfo(self.business_timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("BUSINESS_TIMEZONE must be a valid IANA timezone") from exc


settings = Settings()
