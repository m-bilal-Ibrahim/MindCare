"""FastAPI application factory and default application."""

from fastapi import FastAPI

from src.api.routes.chat import router as chat_router
from src.api.routes.recommend import router as recommend_router


def create_app() -> FastAPI:
    """Create the MindCare API application."""
    application = FastAPI(title="MindCare AI")
    application.include_router(recommend_router)
    application.include_router(chat_router)
    return application


app = create_app()
