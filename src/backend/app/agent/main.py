"""Standalone invoice-agent API. Deliberately does not load the project's .env."""
import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.agent.schemas import AgentHealth, InvoiceEvent
from app.agent.service import InvoiceAgent


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    mandate_api_url: str = "http://api:8000"
    agent_api_key: str = ""


settings = AgentSettings()
app = FastAPI(title="Mandate Invoice Agent", version="0.1.0")


def require_agent_key(x_agent_api_key: Annotated[str, Header(alias="X-Agent-API-Key")] = "") -> None:
    if not settings.agent_api_key or not secrets.compare_digest(
        x_agent_api_key, settings.agent_api_key
    ):
        raise HTTPException(status_code=401, detail="Valid invoice-agent credential required")


@app.get("/health", response_model=AgentHealth)
def health() -> AgentHealth:
    return AgentHealth(status="ok", component="invoice-agent")


@app.post("/api/v1/agent/invoices", dependencies=[Depends(require_agent_key)])
async def process_invoice(invoice: InvoiceEvent) -> JSONResponse:
    status_code, result = await InvoiceAgent(
        settings.mandate_api_url, settings.agent_api_key
    ).process(invoice)
    return JSONResponse(status_code=status_code, content=result)
