"""Stockfish engine wrapper service with connection pooling."""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from stockfish import Stockfish, StockfishException

from app.config import Settings, get_settings
from app.models.responses import AnalysisResult, Evaluation

logger = logging.getLogger(__name__)


class StockfishError(Exception):
    """Custom exception for Stockfish-related errors."""
    
    def __init__(self, message: str, code: str = "ENGINE_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class StockfishPool:
    """
    Connection pool for Stockfish engine instances.
    
    Manages a pool of Stockfish instances to handle concurrent requests
    efficiently while limiting resource usage.
    """
    
    def __init__(
        self,
        pool_size: int = 10,
        stockfish_path: str = "/usr/local/bin/stockfish",
        threads: int = 1,
        hash_size: int = 128,
        skill_level: int = 20,
    ):
        self._pool_size = pool_size
        self._stockfish_path = stockfish_path
        self._threads = threads
        self._hash_size = hash_size
        self._skill_level = skill_level
        self._pool: asyncio.Queue[Stockfish] = asyncio.Queue(maxsize=pool_size)
        self._created_count = 0
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the pool with Stockfish instances."""
        if self._initialized:
            return
        
        async with self._lock:
            if self._initialized:
                return
            
            # Pre-create some instances
            initial_count = min(3, self._pool_size)
            for _ in range(initial_count):
                try:
                    engine = self._create_engine()
                    await self._pool.put(engine)
                    self._created_count += 1
                    logger.info(f"Pre-created Stockfish instance {self._created_count}")
                except Exception as e:
                    logger.warning(f"Failed to pre-create Stockfish instance: {e}")
            
            self._initialized = True
            logger.info(f"Stockfish pool initialized with {self._created_count} instances")
    
    def _create_engine(self) -> Stockfish:
        """Create a new Stockfish instance."""
        try:
            engine = Stockfish(
                path=self._stockfish_path,
                depth=15,
                parameters={
                    "Threads": self._threads,
                    "Hash": self._hash_size,
                    "Skill Level": self._skill_level,
                    "Ponder": False,
                    "MultiPV": 1,
                }
            )
            logger.debug("Created new Stockfish instance")
            return engine
        except Exception as e:
            logger.error(f"Failed to create Stockfish instance: {e}")
            raise StockfishError(
                f"Failed to initialize Stockfish engine: {e}",
                "ENGINE_INIT_ERROR"
            )
    
    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[Stockfish, None]:
        """
        Acquire a Stockfish instance from the pool.
        
        Usage:
            async with pool.acquire() as engine:
                engine.set_fen_position(fen)
                best_move = engine.get_best_move()
        """
        engine: Optional[Stockfish] = None
        
        try:
            # Try to get an existing instance
            try:
                engine = self._pool.get_nowait()
            except asyncio.QueueEmpty:
                # Create a new instance if pool is empty and we haven't hit max
                async with self._lock:
                    if self._created_count < self._pool_size:
                        engine = await asyncio.to_thread(self._create_engine)
                        self._created_count += 1
                
                if engine is None:
                    # Wait for an instance to become available
                    engine = await asyncio.wait_for(
                        self._pool.get(),
                        timeout=30.0  # 30 second timeout
                    )
            
            # Reset engine state for clean usage
            try:
                engine.set_fen_position(
                    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
                )
            except Exception as e:
                logger.warning(f"Engine reset failed, recreating: {e}")
                # Engine might be in bad state, try to recreate
                try:
                    engine = await asyncio.to_thread(self._create_engine)
                except Exception:
                    raise StockfishError("Engine pool exhausted and recreation failed")
            
            yield engine
            
        except asyncio.TimeoutError:
            raise StockfishError(
                "Timeout waiting for available Stockfish instance",
                "TIMEOUT"
            )
        finally:
            if engine is not None:
                try:
                    # Return engine to pool
                    self._pool.put_nowait(engine)
                except asyncio.QueueFull:
                    # Pool is full, close this instance
                    try:
                        engine.__del__()
                    except Exception:
                        pass
    
    async def shutdown(self) -> None:
        """Shutdown all Stockfish instances in the pool."""
        logger.info("Shutting down Stockfish pool...")
        
        while not self._pool.empty():
            try:
                engine = self._pool.get_nowait()
                try:
                    engine.__del__()
                except Exception:
                    pass
            except asyncio.QueueEmpty:
                break
        
        self._created_count = 0
        self._initialized = False
        logger.info("Stockfish pool shutdown complete")


class StockfishService:
    """
    High-level service for interacting with Stockfish engine.
    
    Provides async methods for chess analysis operations with
    connection pooling and proper error handling.
    """
    
    def __init__(self, settings: Settings):
        self._settings = settings
        self._pool = StockfishPool(
            pool_size=settings.max_concurrent_analyses,
            stockfish_path=settings.stockfish_path,
            threads=settings.stockfish_threads,
            hash_size=settings.stockfish_hash_size_mb,
            skill_level=settings.stockfish_skill_level,
        )
        self._start_time = time.time()
    
    @property
    def uptime_seconds(self) -> float:
        """Get service uptime in seconds."""
        return time.time() - self._start_time
    
    async def initialize(self) -> None:
        """Initialize the service and engine pool."""
        await self._pool.initialize()
    
    async def shutdown(self) -> None:
        """Shutdown the service and engine pool."""
        await self._pool.shutdown()
    
    async def is_engine_available(self) -> bool:
        """Check if the Stockfish engine is available."""
        try:
            async with self._pool.acquire() as engine:
                # Simple check - get best move for starting position
                engine.set_fen_position(
                    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
                )
                engine.set_depth(1)
                result = await asyncio.to_thread(engine.get_best_move)
                return result is not None
        except Exception as e:
            logger.error(f"Engine availability check failed: {e}")
            return False
    
    async def get_engine_info(self) -> dict[str, Any]:
        """Get information about the Stockfish engine."""
        try:
            async with self._pool.acquire() as engine:
                info = await asyncio.to_thread(engine.get_stockfish_major_version)
                params = await asyncio.to_thread(engine.get_parameters)
                
                return {
                    "engine": f"Stockfish {info}",
                    "supported_features": [
                        "NNUE",
                        "MultiPV", 
                        "Chess960",
                        "WDL",
                        "Skill Level",
                        "Hash Tables",
                    ],
                    "default_parameters": {
                        "threads": self._settings.stockfish_threads,
                        "hash": self._settings.stockfish_hash_size_mb,
                        "skill_level": self._settings.stockfish_skill_level,
                    }
                }
        except Exception as e:
            logger.error(f"Failed to get engine info: {e}")
            raise StockfishError(f"Failed to get engine info: {e}")
    
    async def get_best_move(
        self,
        fen: str,
        depth: Optional[int] = None,
        time_limit_ms: Optional[int] = None,
        skill_level: Optional[int] = None,
    ) -> AnalysisResult:
        """
        Get the best move for a position.
        
        Args:
            fen: FEN string of the position
            depth: Search depth (overrides default)
            time_limit_ms: Time limit in milliseconds
            skill_level: Engine skill level (0-20)
            
        Returns:
            AnalysisResult with best move and evaluation
        """
        start_time = time.time()
        actual_depth = depth or self._settings.default_depth
        
        async with self._pool.acquire() as engine:
            try:
                # Set skill level if provided
                if skill_level is not None:
                    await asyncio.to_thread(
                        engine.set_skill_level, skill_level
                    )
                else:
                    await asyncio.to_thread(
                        engine.set_skill_level, self._settings.stockfish_skill_level
                    )
                
                # Set depth
                engine.set_depth(actual_depth)
                
                # Set position
                await asyncio.to_thread(engine.set_fen_position, fen)
                
                # Get best move with time limit if specified
                if time_limit_ms:
                    best_move = await asyncio.to_thread(
                        engine.get_best_move_time, time_limit_ms
                    )
                else:
                    best_move = await asyncio.to_thread(engine.get_best_move)
                
                if best_move is None:
                    raise StockfishError(
                        "No legal moves available in this position",
                        "NO_LEGAL_MOVES"
                    )
                
                # Get evaluation
                eval_result = await asyncio.to_thread(engine.get_evaluation)
                evaluation = self._parse_evaluation(eval_result)
                
                # Get principal variation
                top_moves = await asyncio.to_thread(engine.get_top_moves, 1)
                pv_line = []
                if top_moves:
                    pv_line = top_moves[0].get("Move", "").split() if isinstance(top_moves[0].get("Move"), str) else [top_moves[0].get("Move", "")]
                    # Get full PV if available
                    engine_output = await asyncio.to_thread(lambda: engine.info)
                    if "pv" in str(engine_output):
                        # Try to extract PV from engine output
                        pass
                
                # If PV is just the best move, add it
                if not pv_line or pv_line == ['']:
                    pv_line = [best_move]
                
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                return AnalysisResult(
                    best_move=best_move,
                    evaluation=evaluation,
                    depth=actual_depth,
                    pv_line=pv_line,
                    time_ms=elapsed_ms,
                    mate_in=evaluation.value if evaluation.type == "mate" else None,
                )
                
            except StockfishException as e:
                logger.error(f"Stockfish error during analysis: {e}")
                raise StockfishError(f"Engine error: {e}")
    
    async def evaluate_position(
        self,
        fen: str,
        depth: Optional[int] = None,
    ) -> AnalysisResult:
        """
        Evaluate a position without returning best move details.
        
        Args:
            fen: FEN string of the position
            depth: Search depth
            
        Returns:
            AnalysisResult with evaluation
        """
        return await self.get_best_move(fen, depth=depth)
    
    async def get_multi_pv(
        self,
        fen: str,
        num_lines: int = 3,
        depth: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        Get multiple best lines for a position.
        
        Args:
            fen: FEN string of the position
            num_lines: Number of lines to return
            depth: Search depth
            
        Returns:
            List of variations with moves and evaluations
        """
        actual_depth = depth or self._settings.default_depth
        num_lines = min(num_lines, self._settings.max_multi_pv)
        
        async with self._pool.acquire() as engine:
            try:
                engine.set_depth(actual_depth)
                await asyncio.to_thread(engine.set_fen_position, fen)
                
                # Get top moves
                top_moves = await asyncio.to_thread(engine.get_top_moves, num_lines)
                
                variations = []
                for move_info in top_moves:
                    move = move_info.get("Move", "")
                    centipawn = move_info.get("Centipawn")
                    mate = move_info.get("Mate")
                    
                    if mate is not None:
                        evaluation = Evaluation(type="mate", value=mate)
                    elif centipawn is not None:
                        evaluation = Evaluation(type="cp", value=centipawn)
                    else:
                        evaluation = Evaluation(type="cp", value=0)
                    
                    # Get PV for this move (simplified - just the move itself)
                    pv_line = [move] if move else []
                    
                    variations.append({
                        "move": move,
                        "evaluation": evaluation,
                        "pv_line": pv_line,
                    })
                
                return variations
                
            except StockfishException as e:
                logger.error(f"Stockfish error during multi-PV analysis: {e}")
                raise StockfishError(f"Engine error: {e}")
    
    async def get_wdl(self, fen: str, depth: Optional[int] = None) -> dict[str, int]:
        """
        Get Win/Draw/Loss probabilities for a position.
        
        Args:
            fen: FEN string
            depth: Search depth
            
        Returns:
            Dictionary with wdl values
        """
        actual_depth = depth or self._settings.default_depth
        
        async with self._pool.acquire() as engine:
            try:
                engine.set_depth(actual_depth)
                await asyncio.to_thread(engine.set_fen_position, fen)
                
                # Get WDL stats
                wdl = await asyncio.to_thread(engine.get_wdl_stats)
                
                if wdl:
                    return {
                        "win": wdl[0],
                        "draw": wdl[1],
                        "loss": wdl[2],
                    }
                
                return {"win": 0, "draw": 0, "loss": 0}
                
            except StockfishException as e:
                logger.error(f"Stockfish error getting WDL: {e}")
                raise StockfishError(f"Engine error: {e}")
    
    def _parse_evaluation(self, eval_result: dict[str, Any]) -> Evaluation:
        """Parse Stockfish evaluation result to Evaluation model."""
        eval_type = eval_result.get("type", "cp")
        value = eval_result.get("value", 0)
        
        if eval_type == "mate":
            return Evaluation(type="mate", value=value)
        else:
            return Evaluation(type="cp", value=value)


# Singleton instance
_stockfish_service: Optional[StockfishService] = None


async def get_stockfish_service() -> StockfishService:
    """Get or create the StockfishService singleton."""
    global _stockfish_service
    
    if _stockfish_service is None:
        settings = get_settings()
        _stockfish_service = StockfishService(settings)
        await _stockfish_service.initialize()
    
    return _stockfish_service


async def shutdown_stockfish_service() -> None:
    """Shutdown the StockfishService singleton."""
    global _stockfish_service
    
    if _stockfish_service is not None:
        await _stockfish_service.shutdown()
        _stockfish_service = None
