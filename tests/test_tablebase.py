"""Tests for tablebase probe endpoint."""

import pytest
from httpx import AsyncClient


class TestTablebaseProbeEndpoint:
    """Tests for POST /api/v1/tablebase-probe endpoint."""

    @pytest.mark.asyncio
    async def test_tablebase_not_configured(self, client: AsyncClient):
        """Test tablebase returns proper error when not configured."""
        response = await client.post(
            "/api/v1/tablebase-probe",
            json={"fen": "8/8/8/8/8/1k6/8/K7 w - - 0 1"},
        )
        assert response.status_code == 400
        data = response.json()

        assert "error" in data["detail"]
        assert "TABLEBASE_NOT_CONFIGURED" in data["detail"]["error"]["code"]

    @pytest.mark.asyncio
    async def test_tablebase_invalid_fen(self, client: AsyncClient):
        """Test tablebase with invalid FEN."""
        response = await client.post(
            "/api/v1/tablebase-probe",
            json={"fen": "invalid"},
        )
        assert response.status_code == 400
