"""FastAPI Application Entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.core.middleware import (
    PayloadLimitMiddleware,
    RequestLoggingMiddleware,
    register_exception_handlers,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle management."""
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Local-first binding: {settings.HOST}:{settings.PORT}")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


def create_app() -> FastAPI:
    """Builds and configures the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENABLE_OPENAPI else None,
        docs_url="/docs" if settings.ENABLE_OPENAPI else None,
        redoc_url="/redoc" if settings.ENABLE_OPENAPI else None,
        lifespan=lifespan,
    )

    # 1. Register security & error sanitization handlers (NFR-04)
    register_exception_handlers(app)

    # 2. Register custom middlewares (Resource bounds NFR-07, Privacy logging NFR-08)
    app.add_middleware(PayloadLimitMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # 3. CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 4. Include API routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_app()
