from fastapi import FastAPI

from app.controllers import intents


def create_app() -> FastAPI:
    app = FastAPI(title="Mandate", version="0.1.0")
    app.include_router(intents.router)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
