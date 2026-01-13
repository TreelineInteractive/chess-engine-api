"""Move-related endpoints for validation and legal moves."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.requests import (
    LegalMovesRequest,
    ValidateFenRequest,
    ValidateMoveRequest,
)
from app.models.responses import (
    ErrorResponse,
    LegalMovesResponse,
    ValidateFenResponse,
    ValidateMoveResponse,
)
from app.services.analysis_service import AnalysisService, get_analysis_service
from app.utils.validators import validate_fen

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Moves"])


def _validate_fen_or_raise(fen: str) -> None:
    """Validate FEN and raise HTTPException if invalid."""
    is_valid, errors, _ = validate_fen(fen)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_FEN",
                    "message": "The provided FEN string is invalid",
                    "details": "; ".join(errors),
                }
            },
        )


@router.post(
    "/validate-move",
    response_model=ValidateMoveResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid FEN"},
    },
    summary="Validate Move",
    description="""
    Validate a chess move and get detailed information about it.
    
    This endpoint checks if a move is legal in the given position and
    returns detailed information about the move if valid.
    
    **Parameters:**
    - **fen**: Position in FEN notation
    - **move**: Move in UCI notation (e.g., 'e2e4', 'e7e8q' for promotion)
    
    **Returns:**
    - Whether the move is valid
    - Move in SAN notation (if valid)
    - Resulting FEN after the move (if valid)
    - Move classification (capture, castling, check, etc.)
    """,
)
async def validate_move(
    request: ValidateMoveRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> ValidateMoveResponse:
    """Validate a chess move."""
    _validate_fen_or_raise(request.fen)
    
    try:
        return service.validate_move(
            fen=request.fen,
            move=request.move,
        )
    except Exception as e:
        logger.exception(f"Unexpected error in validate-move: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred during move validation",
                    "details": str(e),
                }
            },
        )


@router.post(
    "/legal-moves",
    response_model=LegalMovesResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
    summary="Get Legal Moves",
    description="""
    Get all legal moves for a position, optionally filtered by square.
    
    **Parameters:**
    - **fen**: Position in FEN notation
    - **square**: Optional square to filter moves (e.g., 'e2')
    
    **Returns:**
    - List of legal moves in both UCI and SAN notation
    - Piece on the selected square (if square filter used)
    - Total number of legal moves
    
    **Example:**
    For the starting position with square='e2', returns:
    - e2e3 (e3)
    - e2e4 (e4)
    """,
)
async def get_legal_moves(
    request: LegalMovesRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> LegalMovesResponse:
    """Get all legal moves for a position."""
    _validate_fen_or_raise(request.fen)
    
    try:
        return service.get_legal_moves(
            fen=request.fen,
            square=request.square,
        )
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
    except Exception as e:
        logger.exception(f"Unexpected error in legal-moves: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": str(e),
                }
            },
        )


@router.post(
    "/validate-fen",
    response_model=ValidateFenResponse,
    summary="Validate FEN",
    description="""
    Validate a FEN (Forsyth-Edwards Notation) string.
    
    This endpoint validates the FEN string syntax and chess position validity,
    returning detailed information about the position if valid.
    
    **Validation checks:**
    - Correct FEN syntax (6 parts)
    - Valid piece placement (8 ranks, 8 squares each)
    - Valid active color (w/b)
    - Valid castling rights
    - Valid en passant square
    - Both kings present
    - No pawns on back ranks
    - Side not to move is not in check
    
    **Parameters:**
    - **fen**: FEN string to validate
    
    **Returns:**
    - Whether the FEN is valid
    - List of validation errors (if any)
    - Position information (if valid): side to move, castling rights, etc.
    """,
)
async def validate_fen_endpoint(
    request: ValidateFenRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> ValidateFenResponse:
    """Validate a FEN string."""
    try:
        return service.validate_fen(fen=request.fen)
    except Exception as e:
        logger.exception(f"Unexpected error in validate-fen: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred during FEN validation",
                    "details": str(e),
                }
            },
        )
