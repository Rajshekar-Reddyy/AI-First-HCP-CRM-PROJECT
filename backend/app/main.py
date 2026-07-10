from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, dashboard, hcp, interactions, products, reminders
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import engine
from app.models import Base


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title="AI-First HCP CRM API",
        version="1.0.0",
        description="FastAPI backend for an AI-first healthcare representative CRM.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(chat.router)
    app.include_router(interactions.router)
    app.include_router(hcp.router)
    app.include_router(products.router)
    app.include_router(reminders.router)
    app.include_router(dashboard.router)

    @app.on_event("startup")
    def startup() -> None:
        if settings.create_tables_on_startup:
            Base.metadata.create_all(bind=engine)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "model": settings.groq_model}

    return app


app = create_app()
