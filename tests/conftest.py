"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# Test FEN strings
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
ITALIAN_GAME_FEN = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
SCHOLAR_MATE_FEN = "r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4"
ENDGAME_FEN = "8/8/4k3/8/8/4K3/4P3/8 w - - 0 1"
INVALID_FEN = "invalid fen string"
CHECKMATE_FEN = "rnb1kbnr/pppp1ppp/4p3/8/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
EN_PASSANT_FEN = "rnbqkbnr/ppp2ppp/4p3/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3"


@pytest.fixture
def starting_fen() -> str:
    """Standard starting position FEN."""
    return STARTING_FEN


@pytest.fixture
def italian_game_fen() -> str:
    """Italian Game position FEN."""
    return ITALIAN_GAME_FEN


@pytest.fixture
def endgame_fen() -> str:
    """Simple endgame position FEN."""
    return ENDGAME_FEN


@pytest.fixture
def invalid_fen() -> str:
    """Invalid FEN string."""
    return INVALID_FEN


@pytest.fixture
def checkmate_fen() -> str:
    """Checkmate position FEN."""
    return CHECKMATE_FEN


@pytest.fixture
def en_passant_fen() -> str:
    """Position with en passant available."""
    return EN_PASSANT_FEN
