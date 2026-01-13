"""Engine information and health check endpoints."""

import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.models.requests import EngineConfigRequest, PerftRequest
from app.models.responses import (
    BenchmarkResponse,
    DefaultParameters,
    EngineConfigResponse,
    EngineInfoResponse,
    ErrorResponse,
    HealthResponse,
    PerftResponse,
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


@router.post(
    "/perft",
    response_model=PerftResponse,
    summary="Run Perft Test",
    description="""
    Run a performance test (perft) to count all possible positions from a given position.
    
    Perft is used for move generation testing and debugging. It counts all leaf nodes
    at a given depth, which is useful for validating chess engine correctness.
    
    **Parameters:**
    - `fen`: FEN string or "startpos" for starting position
    - `depth`: Search depth (1-7, limited by MAX_PERFT_DEPTH config)
    - `divide`: If true, return per-move node counts
    
    **Returns:**
    - Total node count
    - Optional per-move breakdown if divide=true
    - Time taken
    """,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        403: {"model": ErrorResponse, "description": "Perft disabled"},
        500: {"model": ErrorResponse, "description": "Engine error"},
    },
)
async def run_perft(
    request: PerftRequest,
    service: Annotated[StockfishService, Depends(get_stockfish_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PerftResponse:
    """Run performance test (perft)."""

    try:
        result = await service.run_perft(
            fen=request.fen,
            depth=request.depth,
            divide=request.divide,
        )

        return PerftResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_INPUT",
                    "message": str(e),
                }
            },
        )
    except StockfishError as e:
        logger.error(f"Stockfish error in perft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                }
            },
        )


@router.get(
    "/benchmark",
    response_model=BenchmarkResponse,
    summary="Run Engine Benchmark",
    description="""
    Run the built-in Stockfish benchmark to measure engine performance.
    
    This executes the `bench` command which analyzes a standard set of positions
    to measure nodes per second (NPS) and overall performance.
    
    **Returns:**
    - Total nodes searched
    - Time taken in milliseconds
    - Nodes per second (NPS)
    """,
    responses={
        403: {"model": ErrorResponse, "description": "Benchmark disabled"},
        500: {"model": ErrorResponse, "description": "Engine error"},
    },
)
async def run_benchmark(
    service: Annotated[StockfishService, Depends(get_stockfish_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> BenchmarkResponse:
    """Run engine benchmark."""

    try:
        result = await service.run_benchmark()
        return BenchmarkResponse(**result)

    except StockfishError as e:
        logger.error(f"Stockfish error in benchmark: {e}")
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
        logger.exception(f"Unexpected error in benchmark: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "BENCHMARK_ERROR",
                    "message": "Failed to run benchmark",
                    "details": str(e),
                }
            },
        )


@router.post(
    "/engine/configure",
    response_model=EngineConfigResponse,
    summary="Update Engine Configuration",
    description="""
    Update Stockfish UCI engine parameters.
    
    **Parameters:**
    - `threads`: Number of CPU threads (1-128)
    - `hash_mb`: Hash table size in MB (1-131072)
    - `skill_level`: Skill level (0-20, 20 is strongest)
    - `move_overhead_ms`: Move overhead in milliseconds
    
    **Returns:**
    - Updated configuration values
    - Success status
    """,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid configuration"},
        500: {"model": ErrorResponse, "description": "Engine error"},
    },
)
async def configure_engine(
    request: EngineConfigRequest,
    service: Annotated[StockfishService, Depends(get_stockfish_service)],
) -> EngineConfigResponse:
    """Update engine configuration."""

    try:
        # Convert request to dictionary, excluding None values
        config_updates = request.model_dump(exclude_none=True)

        result = await service.update_configuration(config_updates)

        return EngineConfigResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_CONFIG",
                    "message": str(e),
                }
            },
        )
    except StockfishError as e:
        logger.error(f"Stockfish error in configure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                }
            },
        )
