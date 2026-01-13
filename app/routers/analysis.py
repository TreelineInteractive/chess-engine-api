"""Analysis endpoints for position and game analysis."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.requests import (
    AnalyzeGameRequest,
    AnalyzePositionRequest,
    BestMoveRequest,
    EvaluateRequest,
    MultiPVRequest,
    OpeningBookRequest,
    WDLStatsRequest,
)
from app.models.responses import (
    AnalyzeGameResponse,
    AnalyzePositionResponse,
    BestMoveResponse,
    ErrorResponse,
    EvaluateResponse,
    MultiPVResponse,
)
from app.services.analysis_service import AnalysisService, get_analysis_service
from app.services.stockfish_service import (
    StockfishError,
    StockfishService,
    get_stockfish_service,
)
from app.utils.validators import validate_fen

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Analysis"])


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
    "/best-move",
    response_model=BestMoveResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Engine error"},
    },
    summary="Get Best Move",
    description="""
    Analyze a chess position and return the best move.
    
    The endpoint accepts a FEN string and optional parameters to control
    the analysis depth, skill level, and time limit.
    
    **Parameters:**
    - **fen**: Position in FEN notation
    - **depth**: Analysis depth (1-25, default: 15)
    - **skill_level**: Engine strength (0-20, default: 20)
    - **time_limit_ms**: Maximum time in milliseconds (100-10000)
    
    **Returns:**
    - Best move in UCI notation
    - Position evaluation (centipawns or mate score)
    - Principal variation (best continuation)
    - Time taken for analysis
    """,
)
async def get_best_move(
    request: BestMoveRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> BestMoveResponse:
    """Get the best move for a chess position."""
    _validate_fen_or_raise(request.fen)

    try:
        return await service.get_best_move(
            fen=request.fen,
            depth=request.depth,
            skill_level=request.skill_level,
            time_limit_ms=request.time_limit_ms,
        )
    except StockfishError as e:
        logger.error(f"Stockfish error in best-move: {e}")
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
        logger.exception(f"Unexpected error in best-move: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "ENGINE_ERROR",
                    "message": "An unexpected error occurred during analysis",
                    "details": str(e),
                }
            },
        )


@router.post(
    "/evaluate",
    response_model=EvaluateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Engine error"},
    },
    summary="Evaluate Position",
    description="""
    Evaluate a chess position and return the evaluation score.
    
    The evaluation includes:
    - Centipawn score (positive = white advantage, negative = black advantage)
    - Mate score if forced mate is found
    - Winning chances percentage for both sides
    
    **Parameters:**
    - **fen**: Position in FEN notation
    - **depth**: Analysis depth (1-25, default: 15)
    
    **Returns:**
    - Position evaluation
    - Mate in N moves (if applicable)
    - Best move
    - Winning chances for both sides
    """,
)
async def evaluate_position(
    request: EvaluateRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> EvaluateResponse:
    """Evaluate a chess position."""
    _validate_fen_or_raise(request.fen)

    try:
        return await service.evaluate_position(
            fen=request.fen,
            depth=request.depth,
        )
    except StockfishError as e:
        logger.error(f"Stockfish error in evaluate: {e}")
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
        logger.exception(f"Unexpected error in evaluate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "ENGINE_ERROR",
                    "message": "An unexpected error occurred during evaluation",
                    "details": str(e),
                }
            },
        )


@router.post(
    "/multi-pv",
    response_model=MultiPVResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Engine error"},
    },
    summary="Multi-PV Analysis",
    description="""
    Get multiple best lines (variations) for a position.
    
    Multi-PV analysis returns the top N best moves along with their
    evaluations and continuations.
    
    **Parameters:**
    - **fen**: Position in FEN notation
    - **depth**: Analysis depth (1-25, default: 15)
    - **num_lines**: Number of best lines to return (1-5, default: 3)
    
    **Returns:**
    - List of top variations with moves and evaluations
    - Analysis depth reached
    """,
)
async def get_multi_pv(
    request: MultiPVRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> MultiPVResponse:
    """Get multiple best lines for a position."""
    _validate_fen_or_raise(request.fen)

    try:
        return await service.get_multi_pv(
            fen=request.fen,
            num_lines=request.num_lines,
            depth=request.depth,
        )
    except StockfishError as e:
        logger.error(f"Stockfish error in multi-pv: {e}")
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
        logger.exception(f"Unexpected error in multi-pv: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "ENGINE_ERROR",
                    "message": "An unexpected error occurred during multi-PV analysis",
                    "details": str(e),
                }
            },
        )


@router.post(
    "/analyze",
    response_model=AnalyzePositionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Engine error"},
    },
    summary="Detailed Position Analysis",
    description="""
    Perform detailed analysis of a chess position.
    
    This endpoint provides comprehensive position analysis including:
    - Evaluation and best move
    - Tactical themes (pins, forks, skewers, etc.)
    - Position type classification (open, closed, tactical, endgame)
    - Material balance
    - Identified threats
    
    **Parameters:**
    - **fen**: Position in FEN notation
    - **depth**: Analysis depth (1-25, default: 18)
    
    **Returns:**
    - Detailed position analysis with tactical information
    """,
)
async def analyze_position(
    request: AnalyzePositionRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> AnalyzePositionResponse:
    """Perform detailed position analysis."""
    _validate_fen_or_raise(request.fen)

    try:
        return await service.analyze_position(
            fen=request.fen,
            depth=request.depth,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_FEN",
                    "message": str(e),
                }
            },
        )
    except StockfishError as e:
        logger.error(f"Stockfish error in analyze: {e}")
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
        logger.exception(f"Unexpected error in analyze: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "ENGINE_ERROR",
                    "message": "An unexpected error occurred during analysis",
                    "details": str(e),
                }
            },
        )


@router.post(
    "/analyze-game",
    response_model=AnalyzeGameResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Engine error"},
    },
    summary="Full Game Analysis",
    description="""
    Analyze a complete chess game move by move.
    
    This endpoint analyzes each move in the game and provides:
    - Move-by-move evaluation and classification
    - Accuracy scores for both players
    - Summary statistics (mistakes, blunders, excellent moves)
    
    **Move Classifications:**
    - **excellent**: Best or near-best move
    - **good**: Minor inaccuracy (< 50 centipawns loss)
    - **inaccuracy**: Noticeable mistake (50-100 centipawns loss)
    - **mistake**: Significant error (100-200 centipawns loss)
    - **blunder**: Serious error (> 200 centipawns loss)
    - **book**: Opening book move
    
    **Parameters:**
    - **moves**: List of moves in UCI notation
    - **starting_fen**: Starting position (default: standard starting position)
    - **depth**: Analysis depth per move (1-20, default: 15)
    
    **Note:** This endpoint may take longer for games with many moves.
    """,
)
async def analyze_game(
    request: AnalyzeGameRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> AnalyzeGameResponse:
    """Analyze a complete chess game."""
    _validate_fen_or_raise(request.starting_fen)

    try:
        return await service.analyze_game(
            moves=request.moves,
            starting_fen=request.starting_fen,
            depth=request.depth,
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
    except StockfishError as e:
        logger.error(f"Stockfish error in analyze-game: {e}")
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
        logger.exception(f"Unexpected error in analyze-game: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "ENGINE_ERROR",
                    "message": "An unexpected error occurred during game analysis",
                    "details": str(e),
                }
            },
        )


@router.post(
    "/wdl-stats",
    response_model=None,
    summary="Get Win/Draw/Loss statistics",
    description="""
    Calculate Win/Draw/Loss probabilities for a chess position using the Lichess formula.
    
    This endpoint evaluates the position and converts the centipawn evaluation into
    win/draw/loss percentages using Lichess's statistical model.
    
    **Formula:**
    - Win% = 50 + 50 × (2 / (1 + e^(-0.00368208 × cp)) - 1)
    - Loss% calculated symmetrically
    - Draw% = 100 - Win% - Loss%
    
    **Parameters:**
    - `fen`: FEN string or "startpos"
    - `depth`: Analysis depth (1-25, default: 20)
    
    **Returns:**
    - Centipawn evaluation
    - Win/Draw/Loss percentages
    - Mate distance if applicable
    """,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid FEN string"},
        500: {"model": ErrorResponse, "description": "Engine error"},
    },
)
async def get_wdl_stats(
    request: WDLStatsRequest,
    service: Annotated[StockfishService, Depends(get_stockfish_service)],
) -> dict:
    """Get Win/Draw/Loss probability statistics for a position."""

    try:
        _validate_fen_or_raise(request.fen)

        result = await service.get_wdl_statistics(fen=request.fen, depth=request.depth)

        return result

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
        logger.error(f"Stockfish error in wdl-stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                }
            },
        )


@router.post(
    "/opening-book",
    response_model=None,
    summary="Look up chess opening",
    description="""
    Identify chess opening name, ECO code, and theory for a sequence of moves.
    
    This endpoint analyzes a sequence of moves and returns information about
    the opening being played, including its name, ECO code, and theoretical
    continuations.
    
    **ECO Code:**
    Encyclopedia of Chess Openings (ECO) classification system:
    - A00-A99: Flank openings
    - B00-B99: Semi-Open games (other than French)
    - C00-C99: Open games and French Defense
    - D00-D99: Closed games and Semi-Closed games
    - E00-E99: Indian defenses
    
    **Parameters:**
    - `moves`: List of moves in UCI or SAN notation
    - `starting_fen`: Optional custom starting position
    
    **Returns:**
    - Opening name
    - ECO code
    - Variation name
    - Theory and typical plans
    """,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid moves"},
    },
)
async def lookup_opening(
    request: OpeningBookRequest,
) -> dict:
    """Look up chess opening information."""
    from app.services.opening_service import get_opening_service

    try:
        opening_service = get_opening_service()
        result = opening_service.lookup_opening(
            moves=request.moves, starting_fen=request.starting_fen
        )

        return result

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
