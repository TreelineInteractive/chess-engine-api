"""Engine information and health check endpoints."""

import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.models.responses import (
    DefaultParameters,
    EngineInfoResponse,
    ErrorResponse,
    HealthResponse,
)
from app.services.stockfish_service import (
    StockfishError,
    StockfishService,
    get_stockfish_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Engine"])

# Track application start time
_start_time = time.time()


@router.get(
    "/engine/info",
    response_model=EngineInfoResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Engine error"},
    },
    summary="Get Engine Information",
    description="""
    Get information about the Stockfish chess engine.
    
    **Returns:**
    - Engine name and version
    - List of supported features (NNUE, MultiPV, Chess960, etc.)
    - Default parameters (threads, hash size, skill level)
    """,
)
async def get_engine_info(
    service: Annotated[StockfishService, Depends(get_stockfish_service)],
) -> EngineInfoResponse:
    """Get Stockfish engine information."""
    try:
        info = await service.get_engine_info()
        
        return EngineInfoResponse(
            engine=info["engine"],
            supported_features=info["supported_features"],
            default_parameters=DefaultParameters(
                threads=info["default_parameters"]["threads"],
                hash=info["default_parameters"]["hash"],
                skill_level=info["default_parameters"]["skill_level"],
            ),
        )
    except StockfishError as e:
        logger.error(f"Stockfish error in engine/info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                }
            },
        )
    except Exception as e:
        logger.exception(f"Unexpected error in engine/info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "ENGINE_ERROR",
                    "message": "Failed to get engine information",
                    "details": str(e),
                }
            },
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="""
    Check the health status of the API service.
    
    This endpoint is suitable for use as a Docker health check or
    load balancer health probe.
    
    **Returns:**
    - Service health status
    - Whether the Stockfish engine is available
    - API version
    - Service uptime in seconds
    """,
)
async def health_check(
    service: Annotated[StockfishService, Depends(get_stockfish_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    """Check service health."""
    try:
        engine_available = await service.is_engine_available()
        uptime = time.time() - _start_time
        
        return HealthResponse(
            status="healthy" if engine_available else "unhealthy",
            engine_available=engine_available,
            version=settings.api_version,
            uptime_seconds=round(uptime, 2),
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        uptime = time.time() - _start_time
        
        return HealthResponse(
            status="unhealthy",
            engine_available=False,
            version=settings.api_version,
            uptime_seconds=round(uptime, 2),
        )


@router.get(
    "/ready",
    response_model=HealthResponse,
    summary="Readiness Check",
    description="""
    Check if the service is ready to accept requests.
    
    Similar to health check, but specifically for Kubernetes readiness probes.
    Returns 503 if the engine is not available.
    
    **Returns:**
    - Service readiness status
    - Engine availability
    - API version
    - Uptime
    """,
)
async def readiness_check(
    service: Annotated[StockfishService, Depends(get_stockfish_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    """Check service readiness."""
    try:
        engine_available = await service.is_engine_available()
        uptime = time.time() - _start_time
        
        if not engine_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": {
                        "code": "NOT_READY",
                        "message": "Engine is not available",
                    }
                },
            )
        
        return HealthResponse(
            status="healthy",
            engine_available=True,
            version=settings.api_version,
            uptime_seconds=round(uptime, 2),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "NOT_READY",
                    "message": "Service is not ready",
                    "details": str(e),
                }
            },
        )
