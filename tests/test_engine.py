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
