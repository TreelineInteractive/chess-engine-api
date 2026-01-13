"""Pydantic response models for the Stockfish API."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class Evaluation(BaseModel):
    """Chess position evaluation."""

    type: Literal["cp", "mate"] = Field(
        ...,
        description="Evaluation type: 'cp' for centipawns, 'mate' for mate score",
    )
    value: int = Field(
        ...,
        description="Evaluation value in centipawns or moves to mate",
    )


class BestMoveResponse(BaseModel):
    """Response model for best move analysis."""

    best_move: str = Field(
        ...,
        description="Best move in UCI notation",
        examples=["e2e4"],
    )
    evaluation: Evaluation = Field(
        ...,
        description="Position evaluation after the move",
    )
    depth: int = Field(
        ...,
        description="Depth reached in analysis",
    )
    pv_line: list[str] = Field(
        ...,
        description="Principal variation (best continuation line)",
    )
    time_taken_ms: int = Field(
        ...,
        description="Time taken for analysis in milliseconds",
    )


class WinningChances(BaseModel):
    """Winning chances for both sides."""

    white: float = Field(
        ...,
        ge=0,
        le=100,
        description="White's winning chances percentage",
    )
    black: float = Field(
        ...,
        ge=0,
        le=100,
        description="Black's winning chances percentage",
    )


class EvaluateResponse(BaseModel):
    """Response model for position evaluation."""

    evaluation: Evaluation = Field(
        ...,
        description="Position evaluation",
    )
    mate_in: Optional[int] = Field(
        default=None,
        description="Moves to forced mate (null if no forced mate)",
    )
    depth: int = Field(
        ...,
        description="Depth reached in analysis",
    )
    best_move: str = Field(
        ...,
        description="Best move in UCI notation",
    )
    winning_chances: WinningChances = Field(
        ...,
        description="Winning probability for each side",
    )


class Variation(BaseModel):
    """A single variation in multi-PV analysis."""

    move: str = Field(
        ...,
        description="Move in UCI notation",
    )
    evaluation: Evaluation = Field(
        ...,
        description="Evaluation after the move",
    )
    pv_line: list[str] = Field(
        ...,
        description="Principal variation for this line",
    )


class MultiPVResponse(BaseModel):
    """Response model for multi-PV analysis."""

    variations: list[Variation] = Field(
        ...,
        description="List of top variations",
    )
    depth: int = Field(
        ...,
        description="Depth reached in analysis",
    )


class MoveType(BaseModel):
    """Classification of a chess move."""

    is_capture: bool = Field(
        ...,
        description="Whether the move captures a piece",
    )
    is_castling: bool = Field(
        ...,
        description="Whether the move is castling",
    )
    is_promotion: bool = Field(
        ...,
        description="Whether the move is a pawn promotion",
    )
    is_check: bool = Field(
        ...,
        description="Whether the move gives check",
    )
    is_checkmate: bool = Field(
        ...,
        description="Whether the move is checkmate",
    )
    is_en_passant: bool = Field(
        default=False,
        description="Whether the move is en passant",
    )


class ValidateMoveResponse(BaseModel):
    """Response model for move validation."""

    valid: bool = Field(
        ...,
        description="Whether the move is legal",
    )
    san: Optional[str] = Field(
        default=None,
        description="Move in Standard Algebraic Notation (if valid)",
    )
    resulting_fen: Optional[str] = Field(
        default=None,
        description="FEN string after the move (if valid)",
    )
    move_type: Optional[MoveType] = Field(
        default=None,
        description="Classification of the move (if valid)",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message (if invalid)",
    )


class LegalMove(BaseModel):
    """A legal chess move."""

    uci: str = Field(
        ...,
        description="Move in UCI notation",
    )
    san: str = Field(
        ...,
        description="Move in Standard Algebraic Notation",
    )
    to_square: str = Field(
        ...,
        description="Destination square",
    )


class LegalMovesResponse(BaseModel):
    """Response model for legal moves query."""

    legal_moves: list[LegalMove] = Field(
        ...,
        description="List of legal moves",
    )
    piece: Optional[str] = Field(
        default=None,
        description="Piece on the selected square (if square was specified)",
    )
    total_moves: int = Field(
        ...,
        description="Total number of legal moves",
    )


class MaterialBalance(BaseModel):
    """Material count for both sides."""

    white: int = Field(
        ...,
        description="White's material value",
    )
    black: int = Field(
        ...,
        description="Black's material value",
    )
    difference: int = Field(
        ...,
        description="Material difference (positive = white advantage)",
    )


class AnalyzePositionResponse(BaseModel):
    """Response model for detailed position analysis."""

    evaluation: Evaluation = Field(
        ...,
        description="Position evaluation",
    )
    best_move: str = Field(
        ...,
        description="Best move in UCI notation",
    )
    threats: list[str] = Field(
        default_factory=list,
        description="List of threats in the position",
    )
    tactical_themes: list[str] = Field(
        default_factory=list,
        description="Identified tactical themes",
    )
    position_type: str = Field(
        default="normal",
        description="Position classification (open, closed, tactical, etc.)",
    )
    material_balance: MaterialBalance = Field(
        ...,
        description="Material count for both sides",
    )


class MoveAnalysis(BaseModel):
    """Analysis of a single move in a game."""

    move_number: int = Field(
        ...,
        description="Move number in the game",
    )
    move: str = Field(
        ...,
        description="Move in UCI notation",
    )
    san: str = Field(
        ...,
        description="Move in SAN notation",
    )
    evaluation_before: Evaluation = Field(
        ...,
        description="Evaluation before the move",
    )
    evaluation_after: Evaluation = Field(
        ...,
        description="Evaluation after the move",
    )
    best_move: str = Field(
        ...,
        description="Best move in the position",
    )
    is_best: bool = Field(
        ...,
        description="Whether the played move was the best",
    )
    classification: str = Field(
        ...,
        description="Move quality (excellent, good, inaccuracy, mistake, blunder, book)",
    )


class AccuracyScore(BaseModel):
    """Accuracy scores for both players."""

    white: float = Field(
        ...,
        ge=0,
        le=100,
        description="White's accuracy percentage",
    )
    black: float = Field(
        ...,
        ge=0,
        le=100,
        description="Black's accuracy percentage",
    )


class GameSummary(BaseModel):
    """Summary statistics for a game analysis."""

    total_moves: int = Field(
        ...,
        description="Total number of moves analyzed",
    )
    accuracy: AccuracyScore = Field(
        ...,
        description="Accuracy scores for both players",
    )
    mistakes: int = Field(
        ...,
        description="Number of mistakes",
    )
    blunders: int = Field(
        ...,
        description="Number of blunders",
    )
    inaccuracies: int = Field(
        default=0,
        description="Number of inaccuracies",
    )
    excellent_moves: int = Field(
        ...,
        description="Number of excellent moves",
    )
    good_moves: int = Field(
        ...,
        description="Number of good moves",
    )
    book_moves: int = Field(
        default=0,
        description="Number of book moves",
    )


class AnalyzeGameResponse(BaseModel):
    """Response model for full game analysis."""

    analysis: list[MoveAnalysis] = Field(
        ...,
        description="Analysis of each move",
    )
    summary: GameSummary = Field(
        ...,
        description="Game summary statistics",
    )


class PositionInfo(BaseModel):
    """Information about a chess position parsed from FEN."""

    to_move: Literal["white", "black"] = Field(
        ...,
        description="Side to move",
    )
    castling_rights: str = Field(
        ...,
        description="Castling rights in FEN notation",
    )
    en_passant: Optional[str] = Field(
        default=None,
        description="En passant target square (if available)",
    )
    halfmove_clock: int = Field(
        ...,
        description="Halfmove clock for 50-move rule",
    )
    fullmove_number: int = Field(
        ...,
        description="Full move number",
    )
    is_check: bool = Field(
        default=False,
        description="Whether the side to move is in check",
    )
    is_checkmate: bool = Field(
        default=False,
        description="Whether the position is checkmate",
    )
    is_stalemate: bool = Field(
        default=False,
        description="Whether the position is stalemate",
    )


class ValidateFenResponse(BaseModel):
    """Response model for FEN validation."""

    valid: bool = Field(
        ...,
        description="Whether the FEN is valid",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of validation errors (if any)",
    )
    position_info: Optional[PositionInfo] = Field(
        default=None,
        description="Position information (if valid)",
    )


class SupportedFeature(BaseModel):
    """A feature supported by the engine."""

    name: str
    enabled: bool = True


class DefaultParameters(BaseModel):
    """Default engine parameters."""

    threads: int
    hash: int
    skill_level: int


class EngineInfoResponse(BaseModel):
    """Response model for engine information."""

    engine: str = Field(
        ...,
        description="Engine name and version",
    )
    supported_features: list[str] = Field(
        ...,
        description="List of supported features",
    )
    default_parameters: DefaultParameters = Field(
        ...,
        description="Default engine parameters",
    )


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: Literal["healthy", "unhealthy"] = Field(
        ...,
        description="Service health status",
    )
    engine_available: bool = Field(
        ...,
        description="Whether the Stockfish engine is available",
    )
    version: str = Field(
        ...,
        description="API version",
    )
    uptime_seconds: float = Field(
        ...,
        description="Service uptime in seconds",
    )


class ErrorDetail(BaseModel):
    """Error detail information."""

    code: str = Field(
        ...,
        description="Error code",
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
    )
    details: Optional[str] = Field(
        default=None,
        description="Additional error details",
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: ErrorDetail = Field(
        ...,
        description="Error information",
    )


class AnalysisResult(BaseModel):
    """Generic analysis result used internally."""

    best_move: str
    evaluation: Evaluation
    depth: int
    pv_line: list[str]
    nodes: Optional[int] = None
    time_ms: Optional[int] = None
    mate_in: Optional[int] = None


class WDLStats(BaseModel):
    """Win/Draw/Loss probability statistics."""

    win: float = Field(..., description="Probability of white winning (0-100)")
    draw: float = Field(..., description="Probability of draw (0-100)")
    loss: float = Field(..., description="Probability of black winning (0-100)")


class WDLStatsResponse(BaseModel):
    """Response model for WDL statistics."""

    wdl: WDLStats = Field(..., description="Win/Draw/Loss probabilities")
    evaluation: Evaluation = Field(..., description="Position evaluation")
    depth: int = Field(..., description="Analysis depth used")
    model: str = Field(
        default="Lichess formula",
        description="WDL calculation model used",
    )
    fen: str = Field(..., description="Position FEN")


class PerftResponse(BaseModel):
    """Response model for perft test."""

    nodes: int = Field(..., description="Total number of leaf nodes")
    depth: int = Field(..., description="Depth searched")
    time_ms: int = Field(..., description="Time taken in milliseconds")
    nps: int = Field(..., description="Nodes per second")
    fen: str = Field(..., description="Position FEN")
    divide: Optional[dict[str, int]] = Field(
        None,
        description="Per-move node counts (only if divide=true)",
    )


class BenchmarkResponse(BaseModel):
    """Response model for benchmark test."""

    total_nodes: int = Field(
        ..., description="Total nodes searched across all positions"
    )
    nodes_per_second: int = Field(..., description="Average nodes per second")
    time_ms: int = Field(..., description="Total time in milliseconds")
    positions_tested: int = Field(
        ..., description="Number of positions in benchmark suite"
    )
    depth: int = Field(..., description="Depth used for benchmark")
    threads: int = Field(..., description="Number of threads used")
    hash_mb: int = Field(..., description="Hash table size in MB")
    signature: str = Field(
        ..., description="Benchmark signature for version verification"
    )


class EngineConfigResponse(BaseModel):
    """Response model for engine configuration updates."""

    updated_parameters: dict[str, Any] = Field(
        ...,
        description="Parameters that were updated",
    )
    current_configuration: dict[str, Any] = Field(
        ...,
        description="Full current engine configuration",
    )
    restart_required: bool = Field(
        default=False,
        description="Whether engine restart is needed",
    )


class OpeningBookResponse(BaseModel):
    """Response model for opening book lookup."""

    opening_name: str = Field(..., description="Name of the opening")
    eco: str = Field(..., description="ECO code (e.g., C50)")
    variation: Optional[str] = Field(None, description="Specific variation name")
    popularity: str = Field(
        ...,
        description="Popularity level: very common, common, uncommon, rare, not in book",
    )
    theory_moves: list[str] = Field(
        ..., description="Common theoretical continuation moves"
    )
    known_until_move: int = Field(
        ...,
        description="Move number until which opening is identified",
    )
    in_book: bool = Field(..., description="Whether position is in opening book")
    fen: str = Field(..., description="Resulting FEN after all moves")


class TablebaseProbeResponse(BaseModel):
    """Response model for tablebase probe."""

    wdl: Literal["win", "draw", "loss", "unknown"] = Field(
        ...,
        description="Win/Draw/Loss result",
    )
    dtz: Optional[int] = Field(
        None, description="Distance to zeroing move (50-move rule)"
    )
    dtm: Optional[int] = Field(None, description="Distance to mate (if available)")
    best_move: Optional[str] = Field(None, description="Best move in UCI notation")
    category: Literal["tablebase", "not_in_tablebase"] = Field(
        ...,
        description="Whether position was found in tablebase",
    )
    pieces: int = Field(..., description="Number of pieces on board")
    fen: str = Field(..., description="Position FEN")
