"""Routers package."""

from app.routers.analysis import router as analysis_router
from app.routers.engine import router as engine_router
from app.routers.moves import router as moves_router
from app.routers.tablebase import router as tablebase_router

__all__ = [
    "analysis_router",
    "moves_router",
    "engine_router",
    "tablebase_router",
]
