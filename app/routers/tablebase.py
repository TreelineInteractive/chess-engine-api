"""Tablebase probe endpoints."""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user

from app.config import Settings, get_settings
from app.models.requests import TablebaseProbeRequest
from app.models.responses import ErrorResponse, TablebaseProbeResponse
from app.services.stockfish_service import (
    StockfishError,
    StockfishService,
    get_stockfish_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Tablebase"])


@router.post(
    "/tablebase-probe",
    response_model=TablebaseProbeResponse,
    summary="Probe Endgame Tablebase",
    description="""
    Query Syzygy endgame tablebases for perfect play in endgame positions.
    
    Tablebases provide definitive answers for positions with 7 pieces or fewer,
    returning win/loss/draw information and distance to mate/conversion.
    
    **Requirements:**
    - Position must have ≤7 pieces total
    - ENABLE_TABLEBASE must be true
    - SYZYGY_PATH must point to valid tablebase files
    
    **Parameters:**
    - `fen`: FEN string of the position to probe
    
    **Returns:**
    - WDL result (win, loss, draw, or cursed-win/blessed-loss)
    - DTZ (distance to zeroing move) if available
    - Whether result is from tablebase
    """,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid FEN or too many pieces"},
        403: {"model": ErrorResponse, "description": "Tablebase disabled"},
        500: {"model": ErrorResponse, "description": "Engine error"},
    },
)
async def probe_tablebase(
    request: TablebaseProbeRequest,
    service: Annotated[StockfishService, Depends(get_stockfish_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    user: Annotated[Optional[dict], Depends(get_current_user)] = None,
) -> TablebaseProbeResponse:
    """Probe Syzygy tablebase."""

    if not settings.syzygy_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "TABLEBASE_NOT_CONFIGURED",
                    "message": "Tablebase path not configured. Set SYZYGY_PATH environment variable.",
                }
            },
        )

    try:
        result = await service.probe_tablebase(fen=request.fen)
        return TablebaseProbeResponse(**result)

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
        logger.error(f"Stockfish error in tablebase-probe: {e}")
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
        logger.exception(f"Unexpected error in tablebase-probe: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "TABLEBASE_ERROR",
                    "message": "Failed to probe tablebase",
                    "details": str(e),
                }
            },
        )
