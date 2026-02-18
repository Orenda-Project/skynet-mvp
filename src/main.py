"""
SkyNet Phase 1 MVP - FastAPI Application Entry Point

This is the main application file that initializes FastAPI and registers routes.
Follows architecture guardrails established for clean, maintainable code.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.utils.logger import setup_logging, logger


# Setup logging first
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        database="Supabase PostgreSQL"
    )

    # TODO: Initialize Supabase database connection pool
    # TODO: Verify external API connections (OpenAI, Whisper, SMTP)

    yield

    # Shutdown
    logger.info("application_shutting_down")
    # TODO: Close database connection pool


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Organizational Intelligence System - Meeting Intelligence + Institutional Memory",
    lifespan=lifespan,
    debug=settings.debug
)


# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint (not versioned - always available)
@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns basic system status.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment
        }
    )


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


# API v1 routes
from src.api.v1 import transcription, synthesis, email

app.include_router(transcription.router)
app.include_router(synthesis.router)
app.include_router(email.router)
# Future routes:
# from src.api.v1 import meetings, search
# app.include_router(meetings.router)
# app.include_router(search.router)


# Global exception handler (Guardrail #7: Error Handling Layers)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler to ensure we never leak internal errors to users.
    Logs full exception details but returns safe message to client.
    """
    logger.error(
        "unhandled_exception",
        path=str(request.url),
        method=request.method,
        error=str(exc),
        exc_info=True
    )

    # In production, never return internal error details
    if settings.is_production:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

    # In development, include error details for debugging
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc),
            "type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
