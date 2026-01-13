"""Tests for engine info and health check endpoints."""

import pytest
from httpx import AsyncClient


class TestEngineInfoEndpoint:
    """Tests for GET /api/v1/engine/info endpoint."""

    @pytest.mark.asyncio
    async def test_engine_info(self, client: AsyncClient):
        """Test getting engine information."""
        response = await client.get("/api/v1/engine/info")

        assert response.status_code == 200
        data = response.json()

        assert "engine" in data
        assert "Stockfish" in data["engine"]
        assert "supported_features" in data
        assert isinstance(data["supported_features"], list)
        assert "default_parameters" in data

        params = data["default_parameters"]
        assert "threads" in params
        assert "hash" in params
        assert "skill_level" in params

    @pytest.mark.asyncio
    async def test_engine_info_features(self, client: AsyncClient):
        """Test that expected features are listed."""
        response = await client.get("/api/v1/engine/info")

        assert response.status_code == 200
        data = response.json()

        features = data["supported_features"]
        assert "NNUE" in features
        assert "MultiPV" in features


class TestHealthEndpoint:
    """Tests for GET /api/v1/health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]
        assert "engine_available" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_health_check_response_time(self, client: AsyncClient):
        """Test that health check responds quickly."""
        import time

        start = time.time()
        response = await client.get("/api/v1/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        # Health check should respond within 5 seconds
        assert elapsed < 5.0


class TestReadinessEndpoint:
    """Tests for GET /api/v1/ready endpoint."""

    @pytest.mark.asyncio
    async def test_readiness_check(self, client: AsyncClient):
        """Test readiness check endpoint."""
        response = await client.get("/api/v1/ready")

        # Should be 200 if engine is available, 503 otherwise
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "healthy"
            assert data["engine_available"] is True


class TestRootEndpoint:
    """Tests for root endpoint."""

    @pytest.mark.asyncio
    async def test_root(self, client: AsyncClient):
        """Test root endpoint returns API info."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "name" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data


class TestOpenAPIEndpoint:
    """Tests for OpenAPI documentation endpoints."""

    @pytest.mark.asyncio
    async def test_openapi_json(self, client: AsyncClient):
        """Test OpenAPI JSON endpoint."""
        response = await client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()

        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    @pytest.mark.asyncio
    async def test_swagger_docs(self, client: AsyncClient):
        """Test Swagger UI endpoint."""
        response = await client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_redoc(self, client: AsyncClient):
        """Test ReDoc endpoint."""
        response = await client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestPerftEndpoint:
    """Tests for POST /api/v1/perft endpoint."""

    @pytest.mark.asyncio
    async def test_perft_starting_position_depth_1(self, client: AsyncClient):
        """Test perft depth 1 returns 20 nodes (20 legal moves)."""
        response = await client.post(
            "/api/v1/perft",
            json={"fen": "startpos", "depth": 1},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["nodes"] == 20
        assert data["depth"] == 1
        assert "time_ms" in data
        assert "nps" in data

    @pytest.mark.asyncio
    async def test_perft_starting_position_depth_3(self, client: AsyncClient):
        """Test perft depth 3 returns 8902 nodes."""
        response = await client.post(
            "/api/v1/perft",
            json={"fen": "startpos", "depth": 3},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["nodes"] == 8902
        assert data["depth"] == 3

    @pytest.mark.asyncio
    async def test_perft_with_divide(self, client: AsyncClient):
        """Test perft with divide mode."""
        response = await client.post(
            "/api/v1/perft",
            json={"fen": "startpos", "depth": 2, "divide": True},
        )
        assert response.status_code == 200
        data = response.json()

        assert "divide" in data
        assert data["divide"] is not None
        assert isinstance(data["divide"], dict)
        # Starting position should have 20 moves
        assert len(data["divide"]) == 20

    @pytest.mark.asyncio
    async def test_perft_custom_position(self, client: AsyncClient):
        """Test perft with custom position."""
        response = await client.post(
            "/api/v1/perft",
            json={
                "fen": "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
                "depth": 2,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nodes"] == 2039  # Known perft value

    @pytest.mark.asyncio
    async def test_perft_depth_too_high(self, client: AsyncClient):
        """Test perft with depth > MAX_PERFT_DEPTH returns validation error."""
        response = await client.post(
            "/api/v1/perft",
            json={"fen": "startpos", "depth": 10},
        )
        assert response.status_code == 422


class TestBenchmarkEndpoint:
    """Tests for GET /api/v1/benchmark endpoint."""

    @pytest.mark.asyncio
    async def test_benchmark_runs(self, client: AsyncClient):
        """Test benchmark endpoint runs successfully."""
        response = await client.get("/api/v1/benchmark")
        assert response.status_code == 200
        data = response.json()

        assert "total_nodes" in data
        assert "nodes_per_second" in data
        assert "time_ms" in data
        assert data["total_nodes"] > 0
        assert data["nodes_per_second"] > 0
        assert data["time_ms"] > 0

    @pytest.mark.asyncio
    async def test_benchmark_returns_metadata(self, client: AsyncClient):
        """Test benchmark returns engine metadata."""
        response = await client.get("/api/v1/benchmark")
        assert response.status_code == 200
        data = response.json()

        assert "positions_tested" in data
        assert "depth" in data
        assert data["positions_tested"] == 50  # Stockfish default


class TestEngineConfigureEndpoint:
    """Tests for POST /api/v1/engine/configure endpoint."""

    @pytest.mark.asyncio
    async def test_configure_threads(self, client: AsyncClient):
        """Test configuring thread count."""
        response = await client.post(
            "/api/v1/engine/configure",
            json={"threads": 4},
        )
        assert response.status_code == 200
        data = response.json()

        assert "updated_parameters" in data
        assert data["updated_parameters"]["threads"] == 4
        assert "current_configuration" in data
        assert data["current_configuration"]["threads"] == 4

    @pytest.mark.asyncio
    async def test_configure_hash_size(self, client: AsyncClient):
        """Test configuring hash table size."""
        response = await client.post(
            "/api/v1/engine/configure",
            json={"hash_mb": 128},  # Use smaller hash for test environment
        )
        assert response.status_code == 200
        data = response.json()

        assert data["updated_parameters"]["hash_mb"] == 128
        assert data["current_configuration"]["hash_mb"] == 128

    @pytest.mark.asyncio
    async def test_configure_multiple_parameters(self, client: AsyncClient):
        """Test configuring multiple parameters at once."""
        response = await client.post(
            "/api/v1/engine/configure",
            json={"threads": 2, "hash_mb": 256, "skill_level": 15},
        )
        assert response.status_code == 200
        data = response.json()

        assert "updated_parameters" in data
        assert len(data["updated_parameters"]) == 3

    @pytest.mark.asyncio
    async def test_configure_invalid_value(self, client: AsyncClient):
        """Test configuration with invalid value returns error."""
        response = await client.post(
            "/api/v1/engine/configure",
            json={"threads": 1000},  # Too many threads
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_configure_no_restart_required(self, client: AsyncClient):
        """Test configuration indicates no restart required."""
        response = await client.post(
            "/api/v1/engine/configure",
            json={"threads": 2},
        )
        assert response.status_code == 200
        data = response.json()

        assert "restart_required" in data
        assert data["restart_required"] is False
