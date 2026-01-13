"""Tests for move validation and legal moves endpoints."""

import pytest
from httpx import AsyncClient

from tests.conftest import EN_PASSANT_FEN, INVALID_FEN, STARTING_FEN


class TestValidateMoveEndpoint:
    """Tests for POST /api/v1/validate-move endpoint."""

    @pytest.mark.asyncio
    async def test_validate_legal_move(self, client: AsyncClient):
        """Test validating a legal move."""
        response = await client.post(
            "/api/v1/validate-move",
            json={"fen": STARTING_FEN, "move": "e2e4"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["san"] == "e4"
        assert "resulting_fen" in data
        assert data["move_type"]["is_capture"] is False
        assert data["move_type"]["is_check"] is False
        assert data["move_type"]["is_castling"] is False
        assert data["move_type"]["is_promotion"] is False

    @pytest.mark.asyncio
    async def test_validate_illegal_move(self, client: AsyncClient):
        """Test validating an illegal move."""
        response = await client.post(
            "/api/v1/validate-move",
            json={"fen": STARTING_FEN, "move": "e2e5"},  # Pawn can't move 3 squares
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "error" in data

    @pytest.mark.asyncio
    async def test_validate_capture_move(self, client: AsyncClient):
        """Test validating a capture move."""
        # Position where white can capture on e5
        fen = "rnbqkbnr/pppp1ppp/8/4p3/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2"
        response = await client.post(
            "/api/v1/validate-move",
            json={"fen": fen, "move": "d4e5"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["move_type"]["is_capture"] is True

    @pytest.mark.asyncio
    async def test_validate_castling_move(self, client: AsyncClient):
        """Test validating a castling move."""
        # Position where white can castle kingside
        fen = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
        response = await client.post(
            "/api/v1/validate-move",
            json={"fen": fen, "move": "e1g1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["move_type"]["is_castling"] is True

    @pytest.mark.asyncio
    async def test_validate_promotion_move(self, client: AsyncClient):
        """Test validating a promotion move."""
        # Position where white pawn can promote
        fen = "8/P7/8/8/8/8/8/4K2k w - - 0 1"
        response = await client.post(
            "/api/v1/validate-move",
            json={"fen": fen, "move": "a7a8q"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["move_type"]["is_promotion"] is True

    @pytest.mark.asyncio
    async def test_validate_check_move(self, client: AsyncClient):
        """Test validating a move that gives check."""
        # Position where Bxf7+ gives check
        fen = "r1bqk2r/pppp1ppp/2n2n2/4p3/2BbP3/2P2N2/PP3PPP/RNBQK2R w KQkq - 0 6"
        response = await client.post(
            "/api/v1/validate-move",
            json={"fen": fen, "move": "c4f7"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        # After Bxf7+, black is in check
        assert data["move_type"]["is_check"] is True
        assert data["move_type"]["is_capture"] is True

    @pytest.mark.asyncio
    async def test_validate_en_passant_move(self, client: AsyncClient):
        """Test validating an en passant move."""
        response = await client.post(
            "/api/v1/validate-move",
            json={"fen": EN_PASSANT_FEN, "move": "e5d6"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["move_type"]["is_capture"] is True
        assert data["move_type"]["is_en_passant"] is True

    @pytest.mark.asyncio
    async def test_validate_move_invalid_fen(self, client: AsyncClient):
        """Test move validation with invalid FEN."""
        response = await client.post(
            "/api/v1/validate-move",
            json={"fen": INVALID_FEN, "move": "e2e4"},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_validate_move_invalid_notation(self, client: AsyncClient):
        """Test move validation with invalid move notation."""
        response = await client.post(
            "/api/v1/validate-move",
            json={"fen": STARTING_FEN, "move": "e4"},  # SAN not UCI
        )

        assert response.status_code == 422  # Validation error


class TestLegalMovesEndpoint:
    """Tests for POST /api/v1/legal-moves endpoint."""

    @pytest.mark.asyncio
    async def test_legal_moves_starting_position(self, client: AsyncClient):
        """Test getting all legal moves for starting position."""
        response = await client.post(
            "/api/v1/legal-moves",
            json={"fen": STARTING_FEN},
        )

        assert response.status_code == 200
        data = response.json()

        assert "legal_moves" in data
        assert "total_moves" in data
        assert data["total_moves"] == 20  # 16 pawn moves + 4 knight moves

        for move in data["legal_moves"]:
            assert "uci" in move
            assert "san" in move
            assert "to_square" in move

    @pytest.mark.asyncio
    async def test_legal_moves_for_square(self, client: AsyncClient):
        """Test getting legal moves for a specific square."""
        response = await client.post(
            "/api/v1/legal-moves",
            json={"fen": STARTING_FEN, "square": "e2"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_moves"] == 2  # e3 and e4
        assert data["piece"] == "P"

        uci_moves = [m["uci"] for m in data["legal_moves"]]
        assert "e2e3" in uci_moves
        assert "e2e4" in uci_moves

    @pytest.mark.asyncio
    async def test_legal_moves_for_knight(self, client: AsyncClient):
        """Test getting legal moves for a knight."""
        response = await client.post(
            "/api/v1/legal-moves",
            json={"fen": STARTING_FEN, "square": "g1"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_moves"] == 2  # Nf3 and Nh3
        assert data["piece"] == "N"

    @pytest.mark.asyncio
    async def test_legal_moves_empty_square(self, client: AsyncClient):
        """Test getting legal moves for an empty square."""
        response = await client.post(
            "/api/v1/legal-moves",
            json={"fen": STARTING_FEN, "square": "e4"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_moves"] == 0
        assert data["piece"] is None

    @pytest.mark.asyncio
    async def test_legal_moves_invalid_square(self, client: AsyncClient):
        """Test legal moves with invalid square notation."""
        response = await client.post(
            "/api/v1/legal-moves",
            json={"fen": STARTING_FEN, "square": "z9"},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_legal_moves_checkmate_position(self, client: AsyncClient):
        """Test legal moves when in checkmate."""
        # Fool's mate position - black is checkmated
        fen = "rnb1kbnr/pppp1ppp/4p3/8/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
        response = await client.post(
            "/api/v1/legal-moves",
            json={"fen": fen},
        )

        assert response.status_code == 200
        data = response.json()
        # White has no legal moves (checkmate)
        assert data["total_moves"] == 0


class TestValidateFenEndpoint:
    """Tests for POST /api/v1/validate-fen endpoint."""

    @pytest.mark.asyncio
    async def test_validate_valid_fen(self, client: AsyncClient):
        """Test validating a valid FEN string."""
        response = await client.post(
            "/api/v1/validate-fen",
            json={"fen": STARTING_FEN},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["errors"] == []
        assert "position_info" in data

        position_info = data["position_info"]
        assert position_info["to_move"] == "white"
        assert position_info["castling_rights"] == "KQkq"
        assert position_info["en_passant"] is None
        assert position_info["halfmove_clock"] == 0
        assert position_info["fullmove_number"] == 1

    @pytest.mark.asyncio
    async def test_validate_invalid_fen(self, client: AsyncClient):
        """Test validating an invalid FEN string."""
        response = await client.post(
            "/api/v1/validate-fen",
            json={"fen": INVALID_FEN},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert len(data["errors"]) > 0
        assert data["position_info"] is None

    @pytest.mark.asyncio
    async def test_validate_fen_with_en_passant(self, client: AsyncClient):
        """Test validating FEN with en passant square."""
        response = await client.post(
            "/api/v1/validate-fen",
            json={"fen": EN_PASSANT_FEN},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["position_info"]["en_passant"] == "d6"

    @pytest.mark.asyncio
    async def test_validate_fen_black_to_move(self, client: AsyncClient):
        """Test validating FEN with black to move."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        response = await client.post(
            "/api/v1/validate-fen",
            json={"fen": fen},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["position_info"]["to_move"] == "black"

    @pytest.mark.asyncio
    async def test_validate_fen_missing_parts(self, client: AsyncClient):
        """Test validating FEN with missing parts."""
        # Only piece placement, missing other parts
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
        response = await client.post(
            "/api/v1/validate-fen",
            json={"fen": fen},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    @pytest.mark.asyncio
    async def test_validate_fen_invalid_castling(self, client: AsyncClient):
        """Test validating FEN with invalid castling rights."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w XYZ - 0 1"
        response = await client.post(
            "/api/v1/validate-fen",
            json={"fen": fen},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    @pytest.mark.asyncio
    async def test_validate_fen_in_check(self, client: AsyncClient):
        """Test validating FEN where side to move is in check."""
        # Position where black is in check from white bishop on f7
        fen = "r1bqk2r/pppp1Bpp/2n2n2/4p3/3bP3/2P2N2/PP3PPP/RNBQK2R b KQkq - 0 6"
        response = await client.post(
            "/api/v1/validate-fen",
            json={"fen": fen},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        # Black is in check from the bishop on f7
        assert data["position_info"]["is_check"] is True
