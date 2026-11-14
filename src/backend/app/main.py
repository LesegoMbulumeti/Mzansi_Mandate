from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.controllers import audit, auth, dashboard, intents, mandates, payees
from app.db.session import SessionLocal
from app.services.errors import ConflictError, IntegrationError, NotFoundError, ValidationError


def create_app() -> FastAPI:
    settings.validate_security_config()
    settings.validate_payment_config()
    settings.validate_business_timezone()
    app = FastAPI(
        title="Mandate API",
        description="Policy-controlled SME payable workflows on XRPL test networks.",
        version="0.2.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Idempotency-Key", "X-Admin-API-Key", "X-Agent-API-Key", "X-Webhook-Secret"],
    )

    for router in (auth.router, intents.router, mandates.router, payees.router, audit.router, dashboard.router):
        app.include_router(router)

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def conflict_handler(_: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def validation_handler(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(IntegrationError)
    async def integration_handler(_: Request, exc: IntegrationError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready", tags=["system"])
    def ready() -> dict[str, str]:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}

    return app


app = create_app()
