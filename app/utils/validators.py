"""Input validation utilities."""

from typing import Optional, Tuple

import chess


class ValidationError(Exception):
    """Custom validation error with code and details."""
    
    def __init__(self, code: str, message: str, details: Optional[str] = None):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


def validate_fen(fen: str) -> Tuple[bool, list[str], Optional[chess.Board]]:
    """
    Validate a FEN string and return detailed error information.
    
    Args:
        fen: FEN string to validate
        
    Returns:
        Tuple of (is_valid, error_list, board_if_valid)
    """
    errors = []
    
    # Check if FEN is empty
    if not fen or not fen.strip():
        errors.append("FEN string is empty")
        return False, errors, None
    
    fen = fen.strip()
    
    # Split into parts
    parts = fen.split()
    
    # Check number of parts (should be 6 for complete FEN)
    if len(parts) != 6:
        errors.append(f"FEN should have 6 parts, got {len(parts)}")
    
    # Validate piece placement (first part)
    if parts:
        ranks = parts[0].split("/")
        if len(ranks) != 8:
            errors.append(f"FEN piece placement should have 8 ranks, got {len(ranks)}")
        else:
            for i, rank in enumerate(ranks):
                count = 0
                for char in rank:
                    if char.isdigit():
                        count += int(char)
                    elif char.lower() in "pnbrqk":
                        count += 1
                    else:
                        errors.append(f"Invalid character '{char}' in rank {8-i}")
                if count != 8:
                    errors.append(f"Rank {8-i} has {count} squares, should have 8")
    
    # Validate active color (second part)
    if len(parts) >= 2:
        if parts[1] not in ["w", "b"]:
            errors.append(f"Invalid active color '{parts[1]}', should be 'w' or 'b'")
    
    # Validate castling rights (third part)
    if len(parts) >= 3:
        if parts[2] != "-":
            valid_chars = set("KQkq")
            for char in parts[2]:
                if char not in valid_chars:
                    errors.append(f"Invalid castling character '{char}'")
    
    # Validate en passant square (fourth part)
    if len(parts) >= 4:
        if parts[3] != "-":
            if len(parts[3]) != 2:
                errors.append(f"Invalid en passant square '{parts[3]}'")
            elif parts[3][0] not in "abcdefgh" or parts[3][1] not in "36":
                errors.append(f"Invalid en passant square '{parts[3]}'")
    
    # Validate halfmove clock (fifth part)
    if len(parts) >= 5:
        try:
            halfmove = int(parts[4])
            if halfmove < 0:
                errors.append("Halfmove clock cannot be negative")
        except ValueError:
            errors.append(f"Invalid halfmove clock '{parts[4]}', must be a number")
    
    # Validate fullmove number (sixth part)
    if len(parts) >= 6:
        try:
            fullmove = int(parts[5])
            if fullmove < 1:
                errors.append("Fullmove number must be at least 1")
        except ValueError:
            errors.append(f"Invalid fullmove number '{parts[5]}', must be a number")
    
    # Try to create a board with python-chess for additional validation
    if not errors:
        try:
            board = chess.Board(fen)
            
            # Check for valid position (kings present, not too many pieces, etc.)
            if not board.is_valid():
                # Get specific validity issues
                status = board.status()
                if status & chess.STATUS_NO_WHITE_KING:
                    errors.append("White king is missing")
                if status & chess.STATUS_NO_BLACK_KING:
                    errors.append("Black king is missing")
                if status & chess.STATUS_TOO_MANY_KINGS:
                    errors.append("Too many kings")
                if status & chess.STATUS_TOO_MANY_WHITE_PAWNS:
                    errors.append("Too many white pawns")
                if status & chess.STATUS_TOO_MANY_BLACK_PAWNS:
                    errors.append("Too many black pawns")
                if status & chess.STATUS_PAWNS_ON_BACKRANK:
                    errors.append("Pawns on back rank")
                if status & chess.STATUS_TOO_MANY_WHITE_PIECES:
                    errors.append("Too many white pieces")
                if status & chess.STATUS_TOO_MANY_BLACK_PIECES:
                    errors.append("Too many black pieces")
                if status & chess.STATUS_OPPOSITE_CHECK:
                    errors.append("Side not to move is in check")
                
                if not errors:
                    errors.append("Invalid position")
                
                return False, errors, None
            
            return True, [], board
            
        except ValueError as e:
            errors.append(str(e))
            return False, errors, None
    
    return False, errors, None


def validate_move_uci(
    move_str: str,
    board: chess.Board,
) -> Tuple[bool, Optional[chess.Move], Optional[str]]:
    """
    Validate a move in UCI notation against a board position.
    
    Args:
        move_str: Move string in UCI notation
        board: Board position
        
    Returns:
        Tuple of (is_valid, move_if_valid, error_message)
    """
    move_str = move_str.strip().lower()
    
    # Basic format check
    if len(move_str) < 4 or len(move_str) > 5:
        return False, None, "Move must be 4-5 characters in UCI notation"
    
    # Try to parse the move
    try:
        move = chess.Move.from_uci(move_str)
    except ValueError as e:
        return False, None, f"Invalid UCI notation: {str(e)}"
    
    # Check if the move is legal
    if move not in board.legal_moves:
        # Try to provide more specific error
        piece = board.piece_at(move.from_square)
        if piece is None:
            return False, None, f"No piece on {chess.square_name(move.from_square)}"
        if piece.color != board.turn:
            return False, None, f"It is not {piece.color}'s turn to move"
        
        # Check if it's a pseudo-legal move (would be legal except for check)
        if move in board.pseudo_legal_moves:
            return False, None, "Move would leave king in check"
        
        return False, None, "Illegal move"
    
    return True, move, None


def validate_square(square_str: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Validate a square notation string.
    
    Args:
        square_str: Square string (e.g., 'e4')
        
    Returns:
        Tuple of (is_valid, square_index, error_message)
    """
    square_str = square_str.strip().lower()
    
    if len(square_str) != 2:
        return False, None, "Square must be exactly 2 characters"
    
    file_char = square_str[0]
    rank_char = square_str[1]
    
    if file_char not in "abcdefgh":
        return False, None, f"Invalid file '{file_char}', must be a-h"
    
    if rank_char not in "12345678":
        return False, None, f"Invalid rank '{rank_char}', must be 1-8"
    
    try:
        square = chess.parse_square(square_str)
        return True, square, None
    except ValueError as e:
        return False, None, str(e)
