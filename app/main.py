"""
Stockfish Chess Engine REST API

A production-ready REST API service that wraps the Stockfish chess engine,
providing HTTP endpoints for chess analysis, move validation, and game evaluation.
"""

import logging
import sys
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.routers import analysis_router, engine_router, moves_router, tablebase_router
from app.services.stockfish_service import shutdown_stockfish_service

# Configure logging
settings = get_settings()


def configure_logging() -> None:
    """Configure structured logging."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    if settings.log_format == "json":
        # JSON structured logging for production
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Console logging for development
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    # Configure root logger
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )


configure_logging()
logger = structlog.get_logger(__name__)


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info(
        "Starting Stockfish API",
        version=settings.api_version,
        debug=settings.debug,
    )

    yield

    # Shutdown
    logger.info("Shutting down Stockfish API")
    await shutdown_stockfish_service()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Stockfish Chess Engine API",
    description="""
A production-ready REST API service that wraps the Stockfish chess engine.

## Features

- **Best Move Analysis**: Get the optimal move for any chess position
- **Position Evaluation**: Evaluate positions with centipawn or mate scores
- **Multi-PV Analysis**: Get multiple best lines for a position
- **Move Validation**: Validate moves and get detailed move information
- **Legal Moves**: List all legal moves for a position
- **Game Analysis**: Analyze complete games with accuracy scores
- **FEN Validation**: Validate FEN strings with detailed error reporting

## Authentication

Currently, no authentication is required. Rate limiting is applied per IP address.

## Rate Limiting

- Default: 100 requests per minute per IP address
- Burst: Up to 10 concurrent requests

## Error Handling

All errors follow a consistent format:
```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable error message",
        "details": "Additional details (optional)"
    }
}
```

## Links

- [Stockfish](https://stockfishchess.org/) - The chess engine
- [python-chess](https://python-chess.readthedocs.io/) - Chess library
    """,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing information."""
    start_time = time.time()

    # Generate request ID
    request_id = str(int(start_time * 1000000))

    # Log request
    logger.info(
        "Request started",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else None,
    )

    try:
        response = await call_next(request)

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Log response
        logger.info(
            "Request completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            response_time_ms=response_time_ms,
        )

        # Add response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{response_time_ms}ms"

        return response

    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)

        logger.error(
            "Request failed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            error=str(e),
            response_time_ms=response_time_ms,
        )
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.exception(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )


# Include routers
app.include_router(analysis_router)
app.include_router(moves_router)
app.include_router(engine_router)
app.include_router(tablebase_router)
app.include_router(tablebase_router)


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Stockfish Chess Engine API",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers,
    )
