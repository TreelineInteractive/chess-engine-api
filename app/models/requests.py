"""Pydantic request models for the Stockfish API."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class BestMoveRequest(BaseModel):
    """Request model for best move analysis."""

    fen: str = Field(
        ...,
        description="FEN string representing the chess position",
        examples=["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"],
    )
    depth: Optional[int] = Field(
        default=None,
        ge=1,
        le=25,
        description="Analysis depth (1-25). Defaults to server configuration.",
    )
    skill_level: Optional[int] = Field(
        default=None,
        ge=0,
        le=20,
        description="Stockfish skill level (0-20). Higher is stronger.",
    )
    time_limit_ms: Optional[int] = Field(
        default=None,
        ge=100,
        le=10000,
        description="Maximum time for analysis in milliseconds (100-10000).",
    )

    @field_validator("fen")
    @classmethod
    def validate_fen_not_empty(cls, v: str) -> str:
        """Validate FEN is not empty."""
        if not v or not v.strip():
            raise ValueError("FEN string cannot be empty")
        return v.strip()


class EvaluateRequest(BaseModel):
    """Request model for position evaluation."""

    fen: str = Field(
        ...,
        description="FEN string representing the chess position",
        examples=["rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"],
    )
    depth: Optional[int] = Field(
        default=None,
        ge=1,
        le=25,
        description="Analysis depth (1-25). Defaults to server configuration.",
    )

    @field_validator("fen")
    @classmethod
    def validate_fen_not_empty(cls, v: str) -> str:
        """Validate FEN is not empty."""
        if not v or not v.strip():
            raise ValueError("FEN string cannot be empty")
        return v.strip()


class MultiPVRequest(BaseModel):
    """Request model for multi-PV analysis."""

    fen: str = Field(
        ...,
        description="FEN string representing the chess position",
        examples=["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"],
    )
    depth: Optional[int] = Field(
        default=None,
        ge=1,
        le=25,
        description="Analysis depth (1-25). Defaults to server configuration.",
    )
    num_lines: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Number of best lines to return (1-5).",
    )

    @field_validator("fen")
    @classmethod
    def validate_fen_not_empty(cls, v: str) -> str:
        """Validate FEN is not empty."""
        if not v or not v.strip():
            raise ValueError("FEN string cannot be empty")
        return v.strip()


class ValidateMoveRequest(BaseModel):
    """Request model for move validation."""

    fen: str = Field(
        ...,
        description="FEN string representing the chess position",
        examples=["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"],
    )
    move: str = Field(
        ...,
        description="Move in UCI notation (e.g., 'e2e4', 'e7e8q' for promotion)",
        examples=["e2e4", "g1f3", "e7e8q"],
        min_length=4,
        max_length=5,
    )

    @field_validator("fen")
    @classmethod
    def validate_fen_not_empty(cls, v: str) -> str:
        """Validate FEN is not empty."""
        if not v or not v.strip():
            raise ValueError("FEN string cannot be empty")
        return v.strip()

    @field_validator("move")
    @classmethod
    def validate_move_format(cls, v: str) -> str:
        """Validate move format."""
        v = v.strip().lower()
        if not v:
            raise ValueError("Move cannot be empty")
        # Basic UCI format validation
        if len(v) < 4 or len(v) > 5:
            raise ValueError("Move must be 4-5 characters in UCI notation")
        return v


class LegalMovesRequest(BaseModel):
    """Request model for legal moves query."""

    fen: str = Field(
        ...,
        description="FEN string representing the chess position",
        examples=["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"],
    )
    square: Optional[str] = Field(
        default=None,
        description="Filter moves for a specific square (e.g., 'e2')",
        examples=["e2", "g1"],
        min_length=2,
        max_length=2,
    )

    @field_validator("fen")
    @classmethod
    def validate_fen_not_empty(cls, v: str) -> str:
        """Validate FEN is not empty."""
        if not v or not v.strip():
            raise ValueError("FEN string cannot be empty")
        return v.strip()

    @field_validator("square")
    @classmethod
    def validate_square_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate square format."""
        if v is None:
            return None
        v = v.strip().lower()
        if len(v) != 2:
            raise ValueError("Square must be exactly 2 characters (e.g., 'e2')")
        if v[0] not in "abcdefgh" or v[1] not in "12345678":
            raise ValueError("Invalid square notation")
        return v


class AnalyzePositionRequest(BaseModel):
    """Request model for detailed position analysis."""

    fen: str = Field(
        ...,
        description="FEN string representing the chess position",
        examples=[
            "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
        ],
    )
    depth: Optional[int] = Field(
        default=None,
        ge=1,
        le=25,
        description="Analysis depth (1-25). Defaults to 18 for detailed analysis.",
    )

    @field_validator("fen")
    @classmethod
    def validate_fen_not_empty(cls, v: str) -> str:
        """Validate FEN is not empty."""
        if not v or not v.strip():
            raise ValueError("FEN string cannot be empty")
        return v.strip()


class AnalyzeGameRequest(BaseModel):
    """Request model for full game analysis."""

    moves: list[str] = Field(
        ...,
        description="List of moves in UCI notation",
        examples=[["e2e4", "e7e5", "g1f3", "b8c6"]],
        min_length=1,
    )
    starting_fen: str = Field(
        default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        description="Starting position FEN. Defaults to standard starting position.",
    )
    depth: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Analysis depth for each move (1-20). Lower values for faster analysis.",
    )

    @field_validator("starting_fen")
    @classmethod
    def validate_fen_not_empty(cls, v: str) -> str:
        """Validate FEN is not empty."""
        if not v or not v.strip():
            raise ValueError("FEN string cannot be empty")
        return v.strip()

    @field_validator("moves")
    @classmethod
    def validate_moves_not_empty(cls, v: list[str]) -> list[str]:
        """Validate moves list is not empty."""
        if not v:
            raise ValueError("Moves list cannot be empty")
        return [move.strip().lower() for move in v]


class ValidateFenRequest(BaseModel):
    """Request model for FEN validation."""

    fen: str = Field(
        ...,
        description="FEN string to validate",
        examples=["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"],
    )

    @field_validator("fen")
    @classmethod
    def validate_fen_not_empty(cls, v: str) -> str:
        """Validate FEN is not empty."""
        if not v or not v.strip():
            raise ValueError("FEN string cannot be empty")
        return v.strip()


from pydantic import BaseModel, Field, field_validator


class WDLStatsRequest(BaseModel):
    """Request model for WDL (Win/Draw/Loss) statistics."""

    fen: str = Field(
        ...,
        description="FEN string of the position to evaluate",
        examples=["rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"],
    )
    depth: int = Field(
        default=15,
        ge=1,
        le=25,
        description="Analysis depth (1-25)",
    )

    @field_validator("fen")
    @classmethod
    def validate_fen_not_empty(cls, v: str) -> str:
        """Validate FEN is not empty and normalize startpos."""
        if not v or not v.strip():
            raise ValueError("FEN string cannot be empty")
        v = v.strip()
        # Normalize "startpos" to starting position FEN
        if v.lower() == "startpos":
            return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        return v


class PerftRequest(BaseModel):
    """Request model for perft (performance test)."""

    fen: str = Field(
        default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        description="FEN string or 'startpos' for starting position",
        examples=[
            "startpos",
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        ],
    )
    depth: int = Field(
        ...,
        ge=1,
        le=7,
        description="Depth to search (1-7, higher is exponentially slower)",
    )
    divide: bool = Field(
        default=False,
        description="Return per-move node counts",
    )

    @field_validator("fen")
    @classmethod
    def validate_fen(cls, v: str) -> str:
        """Validate and normalize FEN."""
        if not v or not v.strip():
            raise ValueError("FEN string cannot be empty")
        v = v.strip()
        if v.lower() == "startpos":
            return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        return v


class EngineConfigRequest(BaseModel):
    """Request model for engine configuration updates."""

    threads: Optional[int] = Field(
        None,
        ge=1,
        le=512,
        description="Number of CPU threads to use",
    )
    hash_mb: Optional[int] = Field(
        None,
        ge=1,
        le=131072,
        description="Hash table size in megabytes",
    )
    skill_level: Optional[int] = Field(
        None,
        ge=0,
        le=20,
        description="Skill level (0=weakest, 20=strongest)",
    )
    uci_limit_strength: Optional[bool] = Field(
        None,
        description="Enable strength limiting (use with uci_elo)",
    )
    uci_elo: Optional[int] = Field(
        None,
        ge=1350,
        le=2850,
        description="Target Elo rating when strength limiting is enabled",
    )
    ponder: Optional[bool] = Field(
        None,
        description="Think on opponent's time",
    )
    multi_pv: Optional[int] = Field(
        None,
        ge=1,
        le=500,
        description="Number of principal variations to calculate",
    )
    uci_chess960: Optional[bool] = Field(
        None,
        description="Enable Chess960 (Fischer Random Chess) mode",
    )


class OpeningBookRequest(BaseModel):
    """Request model for opening book lookup."""

    moves: list[str] = Field(
        ...,
        description="List of moves in UCI notation",
        examples=[["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"]],
        min_length=1,
    )
    starting_fen: str = Field(
        default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        description="Starting position FEN. Defaults to standard starting position.",
    )

    @field_validator("starting_fen")
    @classmethod
    def validate_fen_not_empty(cls, v: str) -> str:
        """Validate FEN is not empty and normalize startpos."""
        if not v or not v.strip():
            raise ValueError("FEN string cannot be empty")
        v = v.strip()
        if v.lower() == "startpos":
            return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        return v

    @field_validator("moves")
    @classmethod
    def validate_moves_not_empty(cls, v: list[str]) -> list[str]:
        """Validate moves list is not empty."""
        if not v:
            raise ValueError("Moves list cannot be empty")
        return [move.strip().lower() for move in v]


class TablebaseProbeRequest(BaseModel):
    """Request model for tablebase probe."""

    fen: str = Field(
        ...,
        description="FEN string of endgame position (7 or fewer pieces)",
        examples=["8/8/8/8/8/4k3/8/4K2R w - - 0 1"],
    )

    @field_validator("fen")
    @classmethod
    def validate_fen_not_empty(cls, v: str) -> str:
        """Validate FEN is not empty."""
        if not v or not v.strip():
            raise ValueError("FEN string cannot be empty")
        return v.strip()
