import secrets

from fastapi import Header, HTTPException

from app.config import settings


def require_operator(x_admin_api_key: str = Header(default="", alias="X-Admin-API-Key")) -> None:
    if not x_admin_api_key or not secrets.compare_digest(x_admin_api_key, settings.admin_api_key):
        raise HTTPException(status_code=401, detail="Valid admin API key required")


def require_intent_client(
    x_admin_api_key: str = Header(default="", alias="X-Admin-API-Key"),
    x_agent_api_key: str = Header(default="", alias="X-Agent-API-Key"),
    x_webhook_secret: str = Header(default="", alias="X-Webhook-Secret"),
) -> None:
    accepted = (
        (x_admin_api_key, settings.admin_api_key),
        (x_agent_api_key, settings.agent_api_key),
        (x_webhook_secret, settings.n8n_shared_secret),
    )
    if not any(provided and secrets.compare_digest(provided, expected) for provided, expected in accepted):
        raise HTTPException(status_code=401, detail="Valid agent, n8n or admin credential required")
