"""Tests for analysis endpoints."""

import pytest
from httpx import AsyncClient

from tests.conftest import (
    CHECKMATE_FEN,
    ENDGAME_FEN,
    INVALID_FEN,
    ITALIAN_GAME_FEN,
    STARTING_FEN,
)


class TestBestMoveEndpoint:
    """Tests for POST /api/v1/best-move endpoint."""

    @pytest.mark.asyncio
    async def test_best_move_starting_position(self, client: AsyncClient):
        """Test getting best move for starting position."""
        response = await client.post(
            "/api/v1/best-move",
            json={"fen": STARTING_FEN},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "best_move" in data
        assert len(data["best_move"]) >= 4  # UCI notation e.g., "e2e4"
        assert "evaluation" in data
        assert data["evaluation"]["type"] in ["cp", "mate"]
        assert "depth" in data
        assert "pv_line" in data
        assert "time_taken_ms" in data

    @pytest.mark.asyncio
    async def test_best_move_with_depth(self, client: AsyncClient):
        """Test best move with custom depth."""
        response = await client.post(
            "/api/v1/best-move",
            json={"fen": STARTING_FEN, "depth": 10},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["depth"] == 10

    @pytest.mark.asyncio
    async def test_best_move_with_skill_level(self, client: AsyncClient):
        """Test best move with custom skill level."""
        response = await client.post(
            "/api/v1/best-move",
            json={"fen": STARTING_FEN, "skill_level": 5},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "best_move" in data

    @pytest.mark.asyncio
    async def test_best_move_with_time_limit(self, client: AsyncClient):
        """Test best move with time limit."""
        response = await client.post(
            "/api/v1/best-move",
            json={"fen": STARTING_FEN, "time_limit_ms": 500},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "best_move" in data

    @pytest.mark.asyncio
    async def test_best_move_invalid_fen(self, client: AsyncClient):
        """Test best move with invalid FEN."""
        response = await client.post(
            "/api/v1/best-move",
            json={"fen": INVALID_FEN},
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "INVALID_FEN"

    @pytest.mark.asyncio
    async def test_best_move_empty_fen(self, client: AsyncClient):
        """Test best move with empty FEN."""
        response = await client.post(
            "/api/v1/best-move",
            json={"fen": ""},
        )
        
        assert response.status_code == 422  # Validation error


class TestEvaluateEndpoint:
    """Tests for POST /api/v1/evaluate endpoint."""

    @pytest.mark.asyncio
    async def test_evaluate_starting_position(self, client: AsyncClient):
        """Test evaluating starting position."""
        response = await client.post(
            "/api/v1/evaluate",
            json={"fen": STARTING_FEN},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "evaluation" in data
        assert data["evaluation"]["type"] in ["cp", "mate"]
        assert "best_move" in data
        assert "winning_chances" in data
        assert "white" in data["winning_chances"]
        assert "black" in data["winning_chances"]
        # Starting position should be roughly equal
        assert 40 <= data["winning_chances"]["white"] <= 60

    @pytest.mark.asyncio
    async def test_evaluate_with_mate(self, client: AsyncClient):
        """Test evaluating a checkmate position."""
        response = await client.post(
            "/api/v1/evaluate",
            json={"fen": CHECKMATE_FEN},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "evaluation" in data

    @pytest.mark.asyncio
    async def test_evaluate_endgame(self, client: AsyncClient):
        """Test evaluating an endgame position."""
        response = await client.post(
            "/api/v1/evaluate",
            json={"fen": ENDGAME_FEN, "depth": 15},
        )
        
        assert response.status_code == 200
        data = response.json()
        # K+P vs K should be winning for white
        assert data["evaluation"]["value"] > 0 or data["evaluation"]["type"] == "mate"


class TestMultiPVEndpoint:
    """Tests for POST /api/v1/multi-pv endpoint."""

    @pytest.mark.asyncio
    async def test_multi_pv_default(self, client: AsyncClient):
        """Test multi-PV with default settings."""
        response = await client.post(
            "/api/v1/multi-pv",
            json={"fen": STARTING_FEN},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "variations" in data
        assert len(data["variations"]) == 3  # Default is 3 lines
        
        for variation in data["variations"]:
            assert "move" in variation
            assert "evaluation" in variation
            assert "pv_line" in variation

    @pytest.mark.asyncio
    async def test_multi_pv_custom_lines(self, client: AsyncClient):
        """Test multi-PV with custom number of lines."""
        response = await client.post(
            "/api/v1/multi-pv",
            json={"fen": STARTING_FEN, "num_lines": 5},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["variations"]) == 5

    @pytest.mark.asyncio
    async def test_multi_pv_single_line(self, client: AsyncClient):
        """Test multi-PV with single line."""
        response = await client.post(
            "/api/v1/multi-pv",
            json={"fen": STARTING_FEN, "num_lines": 1},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["variations"]) == 1


class TestAnalyzeEndpoint:
    """Tests for POST /api/v1/analyze endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_position(self, client: AsyncClient):
        """Test detailed position analysis."""
        response = await client.post(
            "/api/v1/analyze",
            json={"fen": ITALIAN_GAME_FEN},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "evaluation" in data
        assert "best_move" in data
        assert "material_balance" in data
        assert "position_type" in data
        assert "tactical_themes" in data
        
        # Check material balance structure
        assert "white" in data["material_balance"]
        assert "black" in data["material_balance"]
        assert "difference" in data["material_balance"]

    @pytest.mark.asyncio
    async def test_analyze_endgame_position(self, client: AsyncClient):
        """Test analyzing endgame position."""
        response = await client.post(
            "/api/v1/analyze",
            json={"fen": ENDGAME_FEN},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["position_type"] == "endgame"


class TestAnalyzeGameEndpoint:
    """Tests for POST /api/v1/analyze-game endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_short_game(self, client: AsyncClient):
        """Test analyzing a short game."""
        response = await client.post(
            "/api/v1/analyze-game",
            json={
                "moves": ["e2e4", "e7e5", "g1f3", "b8c6"],
                "depth": 10,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "analysis" in data
        assert "summary" in data
        
        # Check analysis structure
        assert len(data["analysis"]) == 4
        for move_analysis in data["analysis"]:
            assert "move_number" in move_analysis
            assert "move" in move_analysis
            assert "san" in move_analysis
            assert "evaluation_before" in move_analysis
            assert "evaluation_after" in move_analysis
            assert "classification" in move_analysis
        
        # Check summary structure
        summary = data["summary"]
        assert "total_moves" in summary
        assert summary["total_moves"] == 4
        assert "accuracy" in summary
        assert "white" in summary["accuracy"]
        assert "black" in summary["accuracy"]

    @pytest.mark.asyncio
    async def test_analyze_game_with_starting_fen(self, client: AsyncClient):
        """Test game analysis with custom starting position."""
        response = await client.post(
            "/api/v1/analyze-game",
            json={
                "moves": ["d7d5", "c2c4"],
                "starting_fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
                "depth": 8,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["analysis"]) == 2

    @pytest.mark.asyncio
    async def test_analyze_game_empty_moves(self, client: AsyncClient):
        """Test game analysis with empty moves list."""
        response = await client.post(
            "/api/v1/analyze-game",
            json={"moves": []},
        )
        
        assert response.status_code == 422  # Validation error
