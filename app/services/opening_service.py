"""Opening book service for chess opening identification."""

import logging
from typing import Any

import chess

logger = logging.getLogger(__name__)


# Simplified opening database with ECO codes
# In production, this would be loaded from a comprehensive database file
OPENING_DATABASE = {
    # Popular openings
    ("e2e4",): {
        "name": "King's Pawn Opening",
        "eco": "B00",
        "variation": None,
        "popularity": "very common",
        "theory_moves": ["e7e5", "c7c5", "e7e6", "c7c6", "d7d6"],
    },
    ("e2e4", "e7e5"): {
        "name": "King's Pawn Game",
        "eco": "C20",
        "variation": None,
        "popularity": "very common",
        "theory_moves": ["g1f3", "f1c4", "d2d4", "f2f4"],
    },
    ("e2e4", "e7e5", "g1f3"): {
        "name": "King's Knight Opening",
        "eco": "C40",
        "variation": None,
        "popularity": "very common",
        "theory_moves": ["b8c6", "g8f6", "d7d6"],
    },
    ("e2e4", "e7e5", "g1f3", "b8c6"): {
        "name": "King's Knight Opening",
        "eco": "C44",
        "variation": None,
        "popularity": "very common",
        "theory_moves": ["f1c4", "f1b5", "d2d4"],
    },
    ("e2e4", "e7e5", "g1f3", "b8c6", "f1c4"): {
        "name": "Italian Game",
        "eco": "C50",
        "variation": "Giuoco Piano",
        "popularity": "very common",
        "theory_moves": ["f8c5", "g8f6"],
    },
    ("e2e4", "e7e5", "g1f3", "b8c6", "f1b5"): {
        "name": "Ruy Lopez",
        "eco": "C60",
        "variation": "Spanish Opening",
        "popularity": "very common",
        "theory_moves": ["a7a6", "g8f6", "f8c5"],
    },
    ("e2e4", "c7c5"): {
        "name": "Sicilian Defense",
        "eco": "B20",
        "variation": None,
        "popularity": "very common",
        "theory_moves": ["g1f3", "b1c3"],
    },
    ("e2e4", "c7c5", "g1f3"): {
        "name": "Sicilian Defense",
        "eco": "B20",
        "variation": "Open Sicilian",
        "popularity": "very common",
        "theory_moves": ["d7d6", "b8c6", "e7e6"],
    },
    ("e2e4", "c7c5", "g1f3", "d7d6"): {
        "name": "Sicilian Defense",
        "eco": "B50",
        "variation": "Modern Variations",
        "popularity": "very common",
        "theory_moves": ["d2d4", "f1c4"],
    },
    ("e2e4", "c7c5", "g1f3", "d7d6", "d2d4"): {
        "name": "Sicilian Defense",
        "eco": "B50",
        "variation": "Open Sicilian",
        "popularity": "very common",
        "theory_moves": ["c5d4", "g8f6"],
    },
    ("e2e4", "e7e6"): {
        "name": "French Defense",
        "eco": "C00",
        "variation": None,
        "popularity": "very common",
        "theory_moves": ["d2d4", "g1f3"],
    },
    ("e2e4", "c7c6"): {
        "name": "Caro-Kann Defense",
        "eco": "B10",
        "variation": None,
        "popularity": "common",
        "theory_moves": ["d2d4", "b1c3"],
    },
    ("d2d4",): {
        "name": "Queen's Pawn Opening",
        "eco": "A40",
        "variation": None,
        "popularity": "very common",
        "theory_moves": ["d7d5", "g8f6", "e7e6"],
    },
    ("d2d4", "d7d5"): {
        "name": "Queen's Pawn Game",
        "eco": "D00",
        "variation": None,
        "popularity": "very common",
        "theory_moves": ["c2c4", "g1f3", "e2e3"],
    },
    ("d2d4", "d7d5", "c2c4"): {
        "name": "Queen's Gambit",
        "eco": "D06",
        "variation": None,
        "popularity": "very common",
        "theory_moves": ["d5c4", "e7e6", "c7c6"],
    },
    ("d2d4", "d7d5", "c2c4", "d5c4"): {
        "name": "Queen's Gambit Accepted",
        "eco": "D20",
        "variation": None,
        "popularity": "very common",
        "theory_moves": ["g1f3", "e2e4"],
    },
    ("d2d4", "d7d5", "c2c4", "e7e6"): {
        "name": "Queen's Gambit Declined",
        "eco": "D30",
        "variation": None,
        "popularity": "very common",
        "theory_moves": ["b1c3", "g1f3"],
    },
    ("d2d4", "g8f6"): {
        "name": "Indian Defense",
        "eco": "A45",
        "variation": None,
        "popularity": "very common",
        "theory_moves": ["c2c4", "g1f3"],
    },
    ("d2d4", "g8f6", "c2c4"): {
        "name": "Indian Game",
        "eco": "E00",
        "variation": None,
        "popularity": "very common",
        "theory_moves": ["e7e6", "g7g6"],
    },
    ("d2d4", "g8f6", "c2c4", "e7e6"): {
        "name": "Indian Defense",
        "eco": "E00",
        "variation": None,
        "popularity": "very common",
        "theory_moves": ["b1c3", "g1f3"],
    },
    ("d2d4", "g8f6", "c2c4", "g7g6"): {
        "name": "King's Indian Defense",
        "eco": "E60",
        "variation": None,
        "popularity": "common",
        "theory_moves": ["b1c3", "g1f3"],
    },
    ("c2c4",): {
        "name": "English Opening",
        "eco": "A10",
        "variation": None,
        "popularity": "common",
        "theory_moves": ["e7e5", "g8f6", "c7c5"],
    },
    ("g1f3",): {
        "name": "Zukertort Opening",
        "eco": "A04",
        "variation": None,
        "popularity": "common",
        "theory_moves": ["d7d5", "g8f6", "c7c5"],
    },
    ("e2e4", "d7d5"): {
        "name": "Scandinavian Defense",
        "eco": "B01",
        "variation": "Center Counter Defense",
        "popularity": "uncommon",
        "theory_moves": ["e4d5", "d2d4"],
    },
    ("e2e4", "g8f6"): {
        "name": "Alekhine's Defense",
        "eco": "B02",
        "variation": None,
        "popularity": "uncommon",
        "theory_moves": ["e4e5", "d2d4"],
    },
}


class OpeningService:
    """Service for looking up chess openings."""

    def lookup_opening(self, moves: list[str], starting_fen: str) -> dict[str, Any]:
        """
        Look up opening information based on move sequence.

        Args:
            moves: List of moves in UCI notation
            starting_fen: Starting position FEN

        Returns:
            Dictionary with opening information
        """
        try:
            # Initialize board
            board = chess.Board(starting_fen)
            move_sequence = []

            # Apply moves
            for move_uci in moves:
                try:
                    move = chess.Move.from_uci(move_uci)
                    if move in board.legal_moves:
                        board.push(move)
                        move_sequence.append(move_uci)
                    else:
                        # Illegal move, stop here
                        break
                except (ValueError, chess.InvalidMoveError):
                    # Invalid move format, stop here
                    break

            # Check for exact match
            move_tuple = tuple(move_sequence)
            if move_tuple in OPENING_DATABASE:
                opening_info = OPENING_DATABASE[move_tuple]
                return {
                    "opening_name": opening_info["name"],
                    "eco": opening_info["eco"],
                    "variation": opening_info["variation"],
                    "popularity": opening_info["popularity"],
                    "theory_moves": opening_info["theory_moves"],
                    "known_until_move": len(move_sequence),
                    "in_book": True,
                    "fen": board.fen(),
                }

            # Check for partial match (longest prefix)
            for i in range(len(move_sequence), 0, -1):
                partial_tuple = tuple(move_sequence[:i])
                if partial_tuple in OPENING_DATABASE:
                    opening_info = OPENING_DATABASE[partial_tuple]
                    return {
                        "opening_name": opening_info["name"],
                        "eco": opening_info["eco"],
                        "variation": opening_info["variation"],
                        "popularity": opening_info["popularity"],
                        "theory_moves": opening_info["theory_moves"],
                        "known_until_move": i,
                        "in_book": True,
                        "fen": board.fen(),
                    }

            # Not in book
            return {
                "opening_name": "Unknown",
                "eco": "???",
                "variation": None,
                "popularity": "not in book",
                "theory_moves": [],
                "known_until_move": 0,
                "in_book": False,
                "fen": board.fen(),
            }

        except Exception as e:
            logger.error(f"Opening lookup failed: {e}")
            raise ValueError(f"Opening lookup failed: {e}")

    def get_theory_moves(self, move_sequence: tuple[str, ...]) -> list[str]:
        """Get theoretical continuation moves for a position."""
        opening_info = OPENING_DATABASE.get(move_sequence)
        if opening_info:
            return opening_info.get("theory_moves", [])
        return []


# Singleton instance
_opening_service: OpeningService | None = None


def get_opening_service() -> OpeningService:
    """Get or create the OpeningService singleton."""
    global _opening_service

    if _opening_service is None:
        _opening_service = OpeningService()

    return _opening_service
