"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from license_tracker.api.v1.router import router as v1_router
from license_tracker.config import get_settings
from license_tracker.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks.

    Args:
        app (FastAPI): FastAPI application instance.

    Yields:
        None: Control to the running application.
    """
    settings = get_settings()
    logger.info("Starting license tracker API (backend={})", settings.app.database_backend)
    await init_db(settings)
    yield
    logger.info("Shutting down license tracker API")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application.

    Returns:
        FastAPI: Configured application.
    """
    settings = get_settings()
    app = FastAPI(
        title="Oracle License Manager",
        version="0.4.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(v1_router)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Log unhandled errors and return a sanitized HTTP 500 response.

        Args:
            request (Request): Incoming HTTP request.
            exc (Exception): Unhandled exception.

        Returns:
            JSONResponse: Sanitized 500 response.
        """
        logger.bind(path=request.url.path).exception("Unhandled server error occurred")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


app = create_app()


def run() -> None:
    """Run the API with uvicorn."""
    import uvicorn

    uvicorn.run(
        "license_tracker.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run()
