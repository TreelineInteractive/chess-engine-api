"""Chess utility functions."""

import math
from typing import Optional

import chess

from app.models.responses import (
    Evaluation,
    MaterialBalance,
    PositionInfo,
    WinningChances,
)


# Piece values for material calculation (standard values)
PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,  # King has no material value
}


def centipawn_to_win_probability(cp: int) -> float:
    """
    Convert centipawn evaluation to winning probability using Lichess formula.
    
    The formula is based on: win_prob = 50 + 50 * (2 / (1 + exp(-0.00368208 * cp)) - 1)
    
    Args:
        cp: Centipawn evaluation (positive = white advantage)
        
    Returns:
        Winning probability for white (0.0 to 100.0)
    """
    # Lichess winning chances formula
    # https://lichess.org/page/accuracy
    try:
        win_prob = 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)
        return round(max(0.0, min(100.0, win_prob)), 1)
    except OverflowError:
        # Handle extreme values
        return 100.0 if cp > 0 else 0.0


def calculate_winning_chances(evaluation: Evaluation) -> WinningChances:
    """
    Calculate winning chances for both sides from an evaluation.
    
    Args:
        evaluation: Position evaluation (centipawns or mate score)
        
    Returns:
        WinningChances with percentages for both sides
    """
    if evaluation.type == "mate":
        # Mate scores: positive = white wins, negative = black wins
        if evaluation.value > 0:
            white_prob = 100.0
        else:
            white_prob = 0.0
    else:
        white_prob = centipawn_to_win_probability(evaluation.value)
    
    return WinningChances(
        white=round(white_prob, 1),
        black=round(100.0 - white_prob, 1),
    )


def calculate_material_balance(board: chess.Board) -> MaterialBalance:
    """
    Calculate the material balance for both sides.
    
    Args:
        board: Chess board position
        
    Returns:
        MaterialBalance with counts for both sides
    """
    white_material = 0
    black_material = 0
    
    for piece_type in PIECE_VALUES:
        white_pieces = len(board.pieces(piece_type, chess.WHITE))
        black_pieces = len(board.pieces(piece_type, chess.BLACK))
        white_material += white_pieces * PIECE_VALUES[piece_type]
        black_material += black_pieces * PIECE_VALUES[piece_type]
    
    return MaterialBalance(
        white=white_material,
        black=black_material,
        difference=white_material - black_material,
    )


def classify_move(
    eval_before: Evaluation,
    eval_after: Evaluation,
    was_best_move: bool,
    is_book_move: bool = False,
) -> str:
    """
    Classify a move based on evaluation change.
    
    Classification thresholds (in centipawns):
    - Blunder: loses > 200 cp or loses forced mate
    - Mistake: loses 100-200 cp
    - Inaccuracy: loses 50-100 cp
    - Good: loses < 50 cp but not best
    - Excellent: best move
    - Book: opening book move
    
    Args:
        eval_before: Evaluation before the move
        eval_after: Evaluation after the move
        was_best_move: Whether the played move was the engine's best
        is_book_move: Whether the move is from opening theory
        
    Returns:
        Classification string
    """
    if is_book_move:
        return "book"
    
    if was_best_move:
        return "excellent"
    
    # Calculate centipawn loss (from the side that moved perspective)
    # After a move, evaluation is from opponent's perspective, so we negate
    if eval_before.type == "mate" and eval_after.type == "mate":
        # Both are mate scores
        if eval_before.value > 0 and eval_after.value < 0:
            # Lost a winning mate
            return "blunder"
        elif eval_before.value < 0 and eval_after.value > 0:
            # Escaped mate (good for the player, but this shouldn't happen as best move)
            return "excellent"
        else:
            # Same side still has mate
            return "good"
    
    if eval_before.type == "mate" and eval_after.type == "cp":
        # Lost a forced mate
        return "blunder"
    
    if eval_before.type == "cp" and eval_after.type == "mate":
        if eval_after.value < 0:
            # Got mated
            return "blunder"
        else:
            # Found a mate (shouldn't be not best, but handle edge case)
            return "excellent"
    
    # Both are centipawn evaluations
    # Note: eval_after is from opponent's perspective, so negate it
    cp_before = eval_before.value
    cp_after = -eval_after.value  # Negate because it's opponent's perspective
    
    cp_loss = cp_before - cp_after
    
    if cp_loss > 200:
        return "blunder"
    elif cp_loss > 100:
        return "mistake"
    elif cp_loss > 50:
        return "inaccuracy"
    else:
        return "good"


def classify_position_type(board: chess.Board) -> str:
    """
    Classify the type of position.
    
    Args:
        board: Chess board position
        
    Returns:
        Position type string (open, closed, tactical, endgame, normal)
    """
    # Count material
    total_pieces = len(board.piece_map())
    
    # Count pawns in center files (d, e)
    center_pawns = 0
    for square in [chess.D2, chess.D3, chess.D4, chess.D5, chess.D6, chess.D7,
                   chess.E2, chess.E3, chess.E4, chess.E5, chess.E6, chess.E7]:
        piece = board.piece_at(square)
        if piece and piece.piece_type == chess.PAWN:
            center_pawns += 1
    
    # Check if in check
    if board.is_check():
        return "tactical"
    
    # Endgame detection (few pieces remaining)
    if total_pieces <= 10:
        return "endgame"
    
    # Count available moves and captures
    legal_moves = list(board.legal_moves)
    captures = [m for m in legal_moves if board.is_capture(m)]
    
    # Tactical position: many captures available
    if len(captures) >= 5:
        return "tactical"
    
    # Closed position: center pawns blocking
    if center_pawns >= 4:
        return "closed"
    
    # Open position: few pawns in center, many open lines
    if center_pawns <= 1 and total_pieces >= 20:
        return "open"
    
    return "normal"


def detect_tactical_themes(
    board: chess.Board,
    best_move: Optional[chess.Move] = None,
) -> list[str]:
    """
    Detect tactical themes in a position.
    
    Args:
        board: Chess board position
        best_move: Best move in the position (optional)
        
    Returns:
        List of detected tactical themes
    """
    themes = []
    
    # Check detection
    if board.is_check():
        themes.append("check")
    
    # Checkmate detection
    if board.is_checkmate():
        themes.append("checkmate")
        return themes  # No need to check other themes
    
    # Fork detection (simplified)
    for move in board.legal_moves:
        if _is_fork(board, move):
            themes.append("fork_threat")
            break
    
    # Pin detection
    if _has_pin(board):
        themes.append("pin")
    
    # Skewer detection (simplified)
    if _has_skewer(board):
        themes.append("skewer")
    
    # Discovered attack potential
    if _has_discovered_attack(board):
        themes.append("discovered_attack")
    
    # En passant availability
    if board.ep_square is not None:
        themes.append("en_passant_available")
    
    # Promotion threat
    for pawn_square in board.pieces(chess.PAWN, board.turn):
        rank = chess.square_rank(pawn_square)
        if (board.turn == chess.WHITE and rank >= 5) or \
           (board.turn == chess.BLACK and rank <= 2):
            themes.append("promotion_threat")
            break
    
    return themes


def _is_fork(board: chess.Board, move: chess.Move) -> bool:
    """Check if a move creates a fork (attacks multiple pieces)."""
    # Make the move on a copy
    test_board = board.copy()
    test_board.push(move)
    
    # Get the piece that moved
    piece = test_board.piece_at(move.to_square)
    if not piece:
        return False
    
    # Count attacked pieces (excluding pawns)
    attacked_pieces = 0
    for attacked_square in test_board.attacks(move.to_square):
        attacked_piece = test_board.piece_at(attacked_square)
        if attacked_piece and attacked_piece.color != piece.color:
            if attacked_piece.piece_type in [chess.KNIGHT, chess.BISHOP, 
                                             chess.ROOK, chess.QUEEN, chess.KING]:
                attacked_pieces += 1
    
    return attacked_pieces >= 2


def _has_pin(board: chess.Board) -> bool:
    """Check if there are any pins in the position."""
    # Check for pins against both kings
    for color in [chess.WHITE, chess.BLACK]:
        king_square = board.king(color)
        if king_square is None:
            continue
        
        # Check if any piece is pinned to the king
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == color and piece.piece_type != chess.KING:
                if board.is_pinned(color, square):
                    return True
    
    return False


def _has_skewer(board: chess.Board) -> bool:
    """Check for skewer patterns (simplified detection)."""
    # Simplified: check for aligned valuable pieces
    # This is a basic heuristic
    for color in [chess.WHITE, chess.BLACK]:
        king_square = board.king(color)
        queen_squares = board.pieces(chess.QUEEN, color)
        rook_squares = board.pieces(chess.ROOK, color)
        
        if king_square and queen_squares:
            for queen_sq in queen_squares:
                # Check if king and queen are on same file/rank/diagonal
                if (chess.square_file(king_square) == chess.square_file(queen_sq) or
                    chess.square_rank(king_square) == chess.square_rank(queen_sq)):
                    # Potential skewer
                    return True
    
    return False


def _has_discovered_attack(board: chess.Board) -> bool:
    """Check for discovered attack potential."""
    # Check if moving a piece could reveal an attack from behind
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == board.turn:
            if piece.piece_type in [chess.KNIGHT, chess.BISHOP, chess.PAWN]:
                # Check if there's a slider behind this piece
                for direction in [8, -8, 1, -1, 7, -7, 9, -9]:
                    check_sq = square + direction
                    if 0 <= check_sq < 64:
                        behind_piece = board.piece_at(check_sq)
                        if behind_piece and behind_piece.color == board.turn:
                            if behind_piece.piece_type in [chess.ROOK, chess.QUEEN, chess.BISHOP]:
                                return True
    return False


def get_piece_symbol(piece: Optional[chess.Piece]) -> Optional[str]:
    """
    Get the FEN symbol for a piece.
    
    Args:
        piece: Chess piece
        
    Returns:
        FEN symbol (uppercase for white, lowercase for black)
    """
    if piece is None:
        return None
    return piece.symbol()


def parse_fen_info(fen: str) -> PositionInfo:
    """
    Parse FEN string and extract position information.
    
    Args:
        fen: FEN string
        
    Returns:
        PositionInfo with parsed data
    """
    board = chess.Board(fen)
    
    parts = fen.split()
    
    # Parse en passant
    ep_square = parts[3] if len(parts) > 3 and parts[3] != "-" else None
    
    # Parse castling
    castling = parts[2] if len(parts) > 2 else "-"
    
    return PositionInfo(
        to_move="white" if board.turn == chess.WHITE else "black",
        castling_rights=castling if castling else "-",
        en_passant=ep_square,
        halfmove_clock=int(parts[4]) if len(parts) > 4 else 0,
        fullmove_number=int(parts[5]) if len(parts) > 5 else 1,
        is_check=board.is_check(),
        is_checkmate=board.is_checkmate(),
        is_stalemate=board.is_stalemate(),
    )
