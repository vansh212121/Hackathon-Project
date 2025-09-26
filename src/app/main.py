from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from typing import Dict, Any

from app.core.config import settings
from app.core.exception_handler import register_exception_handlers
from app.db.session import db

from app.utils.deps import get_health_status
from app.db import base
from app.api.v1.endpoints import user, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    """
    # Startup: Connect to the database
    await db.connect()

    yield

    # Shutdown: Disconnect from the database
    await db.disconnect()


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        lifespan=lifespan,
    )
    # Register all exception handlers
    register_exception_handlers(app)

    app.include_router(auth.router)
    app.include_router(user.router)

    return app


app = create_application()


@app.get("/health", response_model=Dict[str, Any])
async def health_check(health: Dict[str, Any] = Depends(get_health_status)):
    """
    Health check endpoint that provides status and version info.
    """
    return health
