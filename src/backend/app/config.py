from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # SQLite locally, Postgres in docker-compose / production.
    database_url: str = "sqlite:///./mandate.db"
    xrpl_ws_url: str = "wss://s.altnet.rippletest.net:51233"
    # Held ONLY by the Policy Service. The agent process must never read this.
    treasury_address: str = ""
    policy_signer_seed: str = ""
    anthropic_api_key: str = ""
    n8n_shared_secret: str = "change-me"


settings = Settings()
