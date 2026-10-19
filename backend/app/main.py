"""FastAPI Application Entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.api.router import api_router
from app.api.routes.health import get_health
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.core.middleware import (
    PayloadLimitMiddleware,
    RequestLoggingMiddleware,
    register_exception_handlers,
)
from app.db.migrate import run_migrations
from app.db.session import get_db
from app.schemas.health import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle management."""
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Local-first binding: {settings.HOST}:{settings.PORT}")

    if settings.AUTO_MIGRATE:
        run_migrations()

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

    # 4. Root convenience health endpoint (for Docker / K8s probes)
    @app.get("/health", response_model=HealthResponse, tags=["health"])
    def root_health(db: Session = Depends(get_db)) -> HealthResponse:
        return get_health(db)

    # 5. Include API routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # 6. Production Static Assets & SPA Fallback (Phase 4)
    static_dir: Path | None = None
    if settings.STATIC_DIR:
        p = Path(settings.STATIC_DIR).resolve()
        if p.is_dir() and (p / "index.html").is_file():
            static_dir = p
    else:
        candidates = [
            Path(__file__).resolve().parent.parent.parent / "frontend" / "dist",
            Path("/app/frontend/dist"),
            Path("frontend/dist"),
        ]
        for c in candidates:
            if c.is_dir() and (c / "index.html").is_file():
                static_dir = c.resolve()
                break

    if static_dir:
        logger.info(f"Serving SPA static frontend assets from: {static_dir}")
        assets_dir = static_dir / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str) -> FileResponse:
            if (
                full_path.startswith("api/")
                or full_path.startswith("docs")
                or full_path.startswith("redoc")
            ):
                raise HTTPException(status_code=404, detail="Not Found")
            target = static_dir / full_path
            if target.is_file():
                return FileResponse(target)
            return FileResponse(static_dir / "index.html")

    return app


app = create_app()
