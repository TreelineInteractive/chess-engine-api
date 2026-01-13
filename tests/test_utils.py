"""Tests for chess utility functions."""

import chess
import pytest

from app.models.responses import Evaluation, WinningChances
from app.utils.chess_utils import (
    calculate_material_balance,
    calculate_winning_chances,
    centipawn_to_win_probability,
    classify_move,
    classify_position_type,
    detect_tactical_themes,
    get_piece_symbol,
    parse_fen_info,
)
from app.utils.validators import validate_fen, validate_move_uci, validate_square


class TestCentipawnToWinProbability:
    """Tests for centipawn to win probability conversion."""

    def test_equal_position(self):
        """Test that equal position gives roughly 50%."""
        prob = centipawn_to_win_probability(0)
        assert 49 <= prob <= 51

    def test_white_advantage(self):
        """Test white advantage gives higher probability."""
        prob = centipawn_to_win_probability(100)
        assert prob > 55

    def test_black_advantage(self):
        """Test black advantage gives lower probability."""
        prob = centipawn_to_win_probability(-100)
        assert prob < 45

    def test_winning_position(self):
        """Test winning position approaches 100%."""
        prob = centipawn_to_win_probability(1000)
        assert prob > 95

    def test_losing_position(self):
        """Test losing position approaches 0%."""
        prob = centipawn_to_win_probability(-1000)
        assert prob < 5

    def test_extreme_values(self):
        """Test extreme values don't cause errors."""
        prob_high = centipawn_to_win_probability(10000)
        prob_low = centipawn_to_win_probability(-10000)

        assert 0 <= prob_high <= 100
        assert 0 <= prob_low <= 100


class TestCalculateWinningChances:
    """Tests for winning chances calculation."""

    def test_equal_position(self):
        """Test equal position gives roughly 50-50."""
        eval_ = Evaluation(type="cp", value=0)
        chances = calculate_winning_chances(eval_)

        assert isinstance(chances, WinningChances)
        assert 45 <= chances.white <= 55
        assert 45 <= chances.black <= 55
        assert abs(chances.white + chances.black - 100) < 0.1

    def test_mate_for_white(self):
        """Test mate for white gives 100% for white."""
        eval_ = Evaluation(type="mate", value=5)
        chances = calculate_winning_chances(eval_)

        assert chances.white == 100.0
        assert chances.black == 0.0

    def test_mate_for_black(self):
        """Test mate for black gives 0% for white."""
        eval_ = Evaluation(type="mate", value=-5)
        chances = calculate_winning_chances(eval_)

        assert chances.white == 0.0
        assert chances.black == 100.0


class TestCalculateMaterialBalance:
    """Tests for material balance calculation."""

    def test_starting_position(self):
        """Test starting position has equal material."""
        board = chess.Board()
        balance = calculate_material_balance(board)

        assert balance.white == balance.black
        assert balance.difference == 0
        # 8 pawns + 2 knights + 2 bishops + 2 rooks + 1 queen = 39
        assert balance.white == 39

    def test_material_advantage(self):
        """Test position with material advantage."""
        # White has extra queen
        board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        board.remove_piece_at(chess.D8)  # Remove black queen

        balance = calculate_material_balance(board)
        assert balance.difference == 9  # Queen is worth 9


class TestClassifyMove:
    """Tests for move classification."""

    def test_excellent_move(self):
        """Test that best move is classified as excellent."""
        eval_before = Evaluation(type="cp", value=0)
        eval_after = Evaluation(type="cp", value=0)

        classification = classify_move(eval_before, eval_after, was_best_move=True)
        assert classification == "excellent"

    def test_blunder(self):
        """Test that large cp loss is a blunder."""
        eval_before = Evaluation(type="cp", value=100)
        eval_after = Evaluation(
            type="cp", value=200
        )  # After opponent moves, it's from their perspective

        classification = classify_move(eval_before, eval_after, was_best_move=False)
        assert classification == "blunder"

    def test_book_move(self):
        """Test that book move is classified correctly."""
        eval_before = Evaluation(type="cp", value=10)
        eval_after = Evaluation(type="cp", value=-10)

        classification = classify_move(
            eval_before, eval_after, was_best_move=False, is_book_move=True
        )
        assert classification == "book"


class TestClassifyPositionType:
    """Tests for position type classification."""

    def test_starting_position(self):
        """Test starting position is closed (4 center pawns)."""
        board = chess.Board()
        position_type = classify_position_type(board)
        # Starting position has 4 pawns in center squares (d4, d5, e4, e5)
        # so it's classified as 'closed'
        assert position_type == "closed"

    def test_endgame(self):
        """Test endgame detection."""
        board = chess.Board("8/8/4k3/8/8/4K3/4P3/8 w - - 0 1")
        position_type = classify_position_type(board)
        assert position_type == "endgame"


class TestDetectTacticalThemes:
    """Tests for tactical theme detection."""

    def test_check_detection(self):
        """Test check detection."""
        board = chess.Board(
            "rnbqkbnr/ppppp1pp/5p2/7Q/4P3/8/PPPP1PPP/RNB1KBNR b KQkq - 1 2"
        )
        themes = detect_tactical_themes(board)
        assert "check" in themes

    def test_promotion_threat(self):
        """Test promotion threat detection."""
        board = chess.Board("8/P7/8/8/8/8/8/4K2k w - - 0 1")
        themes = detect_tactical_themes(board)
        assert "promotion_threat" in themes


class TestValidateFen:
    """Tests for FEN validation."""

    def test_valid_starting_fen(self):
        """Test valid starting position."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        is_valid, errors, board = validate_fen(fen)

        assert is_valid is True
        assert errors == []
        assert board is not None

    def test_invalid_fen_structure(self):
        """Test FEN with wrong number of parts."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w"
        is_valid, errors, board = validate_fen(fen)

        assert is_valid is False
        assert len(errors) > 0

    def test_invalid_piece_placement(self):
        """Test FEN with invalid piece placement."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP w KQkq - 0 1"  # Missing rank
        is_valid, errors, board = validate_fen(fen)

        assert is_valid is False

    def test_missing_king(self):
        """Test FEN with missing king."""
        fen = "rnbq1bnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"  # Missing black king
        is_valid, errors, board = validate_fen(fen)

        assert is_valid is False


class TestValidateMoveUCI:
    """Tests for UCI move validation."""

    def test_valid_move(self):
        """Test valid move."""
        board = chess.Board()
        is_valid, move, error = validate_move_uci("e2e4", board)

        assert is_valid is True
        assert move is not None
        assert error is None

    def test_invalid_move(self):
        """Test invalid move."""
        board = chess.Board()
        is_valid, move, error = validate_move_uci(
            "e2e5", board
        )  # Pawn can't go 3 squares

        assert is_valid is False
        assert move is None
        assert error is not None

    def test_move_from_empty_square(self):
        """Test move from empty square."""
        board = chess.Board()
        is_valid, move, error = validate_move_uci("e4e5", board)

        assert is_valid is False
        assert "No piece" in error


class TestValidateSquare:
    """Tests for square validation."""

    def test_valid_square(self):
        """Test valid square."""
        is_valid, square, error = validate_square("e4")

        assert is_valid is True
        assert square == chess.E4
        assert error is None

    def test_invalid_file(self):
        """Test invalid file."""
        is_valid, square, error = validate_square("z4")

        assert is_valid is False
        assert error is not None

    def test_invalid_rank(self):
        """Test invalid rank."""
        is_valid, square, error = validate_square("e9")

        assert is_valid is False
        assert error is not None


class TestGetPieceSymbol:
    """Tests for piece symbol getter."""

    def test_white_pawn(self):
        """Test white pawn symbol."""
        piece = chess.Piece(chess.PAWN, chess.WHITE)
        assert get_piece_symbol(piece) == "P"

    def test_black_knight(self):
        """Test black knight symbol."""
        piece = chess.Piece(chess.KNIGHT, chess.BLACK)
        assert get_piece_symbol(piece) == "n"

    def test_none(self):
        """Test None piece."""
        assert get_piece_symbol(None) is None


class TestParseFenInfo:
    """Tests for FEN info parsing."""

    def test_starting_position(self):
        """Test parsing starting position."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        info = parse_fen_info(fen)

        assert info.to_move == "white"
        assert info.castling_rights == "KQkq"
        assert info.en_passant is None
        assert info.halfmove_clock == 0
        assert info.fullmove_number == 1
        assert info.is_check is False

    def test_black_to_move(self):
        """Test parsing position with black to move."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        info = parse_fen_info(fen)

        assert info.to_move == "black"
        assert info.en_passant == "e3"
