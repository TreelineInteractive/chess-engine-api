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
            logger.info(
                f"Stockfish pool initialized with {self._created_count} instances"
            )

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
                },
            )
            logger.debug("Created new Stockfish instance")
            return engine
        except Exception as e:
            logger.error(f"Failed to create Stockfish instance: {e}")
            raise StockfishError(
                f"Failed to initialize Stockfish engine: {e}", "ENGINE_INIT_ERROR"
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
        engine_crashed = False

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
                        self._pool.get(), timeout=30.0  # 30 second timeout
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

        except StockfishException:
            engine_crashed = True
            raise
        except asyncio.TimeoutError:
            raise StockfishError(
                "Timeout waiting for available Stockfish instance", "TIMEOUT"
            )
        finally:
            if engine is not None:
                if engine_crashed:
                    # Discard crashed engines instead of returning them to the pool
                    logger.warning("Discarding crashed Stockfish instance, will recreate on next request")
                    try:
                        engine.__del__()
                    except Exception:
                        pass
                else:
                    try:
                        self._pool.put_nowait(engine)
                    except asyncio.QueueFull:
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
                params = await asyncio.to_thread(engine.get_engine_parameters)

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
                    },
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
                    await asyncio.to_thread(engine.set_skill_level, skill_level)
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
                        "No legal moves available in this position", "NO_LEGAL_MOVES"
                    )

                # Get evaluation
                eval_result = await asyncio.to_thread(engine.get_evaluation)
                evaluation = self._parse_evaluation(eval_result)

                # Get principal variation
                top_moves = await asyncio.to_thread(engine.get_top_moves, 1)
                pv_line = []
                if top_moves:
                    pv_line = (
                        top_moves[0].get("Move", "").split()
                        if isinstance(top_moves[0].get("Move"), str)
                        else [top_moves[0].get("Move", "")]
                    )
                    # Get full PV if available
                    engine_output = await asyncio.to_thread(lambda: engine.info)
                    if "pv" in str(engine_output):
                        # Try to extract PV from engine output
                        pass

                # If PV is just the best move, add it
                if not pv_line or pv_line == [""]:
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

                    variations.append(
                        {
                            "move": move,
                            "evaluation": evaluation,
                            "pv_line": pv_line,
                        }
                    )

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

    async def get_wdl_statistics(self, fen: str, depth: int) -> dict[str, Any]:
        """
        Get Win/Draw/Loss statistics for a position using Lichess formula.

        Args:
            fen: FEN string of the position
            depth: Analysis depth

        Returns:
            Dictionary with WDL stats and evaluation
        """
        async with self._pool.acquire() as engine:
            start_time = time.time()

            try:
                # Set position
                engine.set_fen_position(fen)

                # Set depth
                engine.set_depth(depth)

                # Get evaluation
                evaluation = engine.get_evaluation()

                # Calculate WDL using Lichess formula
                wdl = self._calculate_wdl(evaluation)

                return {
                    "wdl": wdl,
                    "evaluation": self._parse_evaluation(evaluation),
                    "depth": depth,
                    "model": "Lichess formula",
                    "fen": fen,
                    "time_ms": int((time.time() - start_time) * 1000),
                }

            except Exception as e:
                logger.error(f"WDL analysis failed: {e}")
                raise StockfishError(f"WDL analysis failed: {e}")

    def _calculate_wdl(self, evaluation: dict[str, Any]) -> dict[str, float]:
        """
        Calculate Win/Draw/Loss probabilities using Lichess formula.

        Win% = 50 + 50 * (2 / (1 + exp(-0.00368208 * cp)) - 1)
        """
        import math

        eval_type = evaluation.get("type", "cp")
        value = evaluation.get("value", 0)

        if eval_type == "mate":
            # Mate positions
            if value > 0:
                return {"win": 100.0, "draw": 0.0, "loss": 0.0}
            else:
                return {"win": 0.0, "draw": 0.0, "loss": 100.0}

        # Centipawn evaluation
        cp = value

        # Lichess formula
        win_pct = 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)
        loss_pct = 100 - win_pct

        # Approximate draw rate (higher for balanced positions)
        draw_pct = max(0, 40 * math.exp(-abs(cp) / 100))

        # Normalize to sum to 100
        total = win_pct + draw_pct + loss_pct

        return {
            "win": round((win_pct / total) * 100, 1),
            "draw": round((draw_pct / total) * 100, 1),
            "loss": round((loss_pct / total) * 100, 1),
        }

    async def run_perft(
        self, fen: str, depth: int, divide: bool = False
    ) -> dict[str, Any]:
        """
        Run perft (performance test) on a position.

        Args:
            fen: FEN string of the position
            depth: Depth to search
            divide: Whether to return per-move node counts

        Returns:
            Dictionary with perft results
        """
        import chess

        start_time = time.time()

        try:
            board = chess.Board(fen)

            if divide:
                # Run divide perft
                divide_results = {}
                total_nodes = 0

                for move in board.legal_moves:
                    board.push(move)
                    nodes = await asyncio.to_thread(self._perft_inner, board, depth - 1)
                    board.pop()
                    divide_results[move.uci()] = nodes
                    total_nodes += nodes

                time_ms = int((time.time() - start_time) * 1000)

                return {
                    "nodes": total_nodes,
                    "depth": depth,
                    "time_ms": time_ms,
                    "nps": int(total_nodes / (time_ms / 1000)) if time_ms > 0 else 0,
                    "fen": fen,
                    "divide": divide_results,
                }
            else:
                # Run regular perft
                total_nodes = await asyncio.to_thread(self._perft_inner, board, depth)
                time_ms = int((time.time() - start_time) * 1000)

                return {
                    "nodes": total_nodes,
                    "depth": depth,
                    "time_ms": time_ms,
                    "nps": int(total_nodes / (time_ms / 1000)) if time_ms > 0 else 0,
                    "fen": fen,
                    "divide": None,
                }

        except Exception as e:
            logger.error(f"Perft failed: {e}")
            raise StockfishError(f"Perft failed: {e}")

    def _perft_inner(self, board, depth: int) -> int:
        """Inner perft function (runs in thread)."""
        import chess

        if depth == 0:
            return 1

        nodes = 0
        for move in board.legal_moves:
            board.push(move)
            nodes += self._perft_inner(board, depth - 1)
            board.pop()

        return nodes

    async def run_benchmark(self, depth: Optional[int] = None) -> dict[str, Any]:
        """
        Run Stockfish benchmark.

        Args:
            depth: Optional custom depth

        Returns:
            Dictionary with benchmark results
        """
        import re
        import subprocess

        try:
            cmd = [self._settings.stockfish_path, "bench"]
            if depth:
                cmd.append(str(depth))

            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                timeout=self._settings.benchmark_timeout_seconds,
            )

            output = result.stdout + result.stderr

            # Parse output
            time_match = re.search(r"Total time \(ms\)\s*:\s*(\d+)", output)
            nodes_match = re.search(r"Nodes searched\s*:\s*(\d+)", output)
            nps_match = re.search(r"Nodes/second\s*:\s*(\d+)", output)

            time_ms = int(time_match.group(1)) if time_match else 0
            total_nodes = int(nodes_match.group(1)) if nodes_match else 0
            nps = int(nps_match.group(1)) if nps_match else 0

            return {
                "total_nodes": total_nodes,
                "nodes_per_second": nps,
                "time_ms": time_ms,
                "positions_tested": 50,
                "depth": depth or 13,
                "threads": self._settings.stockfish_threads,
                "hash_mb": self._settings.stockfish_hash_size_mb,
                "signature": str(total_nodes),
            }

        except subprocess.TimeoutExpired:
            raise StockfishError("Benchmark timeout exceeded")
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            raise StockfishError(f"Benchmark failed: {e}")

    async def update_configuration(
        self, config_updates: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Update Stockfish UCI configuration.

        Args:
            config_updates: Dictionary of configuration parameters to update

        Returns:
            Dictionary with updated parameters and current configuration
        """
        UCI_OPTION_MAP = {
            "threads": "Threads",
            "hash_mb": "Hash",
            "skill_level": "Skill Level",
            "uci_limit_strength": "UCI_LimitStrength",
            "uci_elo": "UCI_Elo",
            "ponder": "Ponder",
            "multi_pv": "MultiPV",
            "uci_chess960": "UCI_Chess960",
        }

        updated = {}

        async with self._pool.acquire() as engine:
            try:
                for param, value in config_updates.items():
                    if value is not None:
                        uci_option = UCI_OPTION_MAP.get(param)
                        if uci_option:
                            engine.update_engine_parameters({uci_option: value})
                            updated[param] = value

                # Get current configuration
                params = engine.get_engine_parameters()
                current_config = {
                    "threads": params.get("Threads", 1),
                    "hash_mb": params.get("Hash", 128),
                    "skill_level": params.get("Skill Level", 20),
                    "ponder": params.get("Ponder", False),
                    "multi_pv": params.get("MultiPV", 1),
                }

                return {
                    "updated_parameters": updated,
                    "current_configuration": current_config,
                    "restart_required": False,
                }

            except Exception as e:
                logger.error(f"Configuration update failed: {e}")
                raise StockfishError(f"Configuration update failed: {e}")

    async def probe_tablebase(self, fen: str) -> dict[str, Any]:
        """
        Probe Syzygy tablebase for endgame positions.

        Args:
            fen: FEN string of endgame position

        Returns:
            Dictionary with tablebase probe results
        """
        import chess

        try:
            board = chess.Board(fen)
            piece_count = len(board.piece_map())

            if piece_count > 7:
                return {
                    "wdl": "unknown",
                    "dtz": None,
                    "dtm": None,
                    "best_move": None,
                    "category": "not_in_tablebase",
                    "pieces": piece_count,
                    "fen": fen,
                }

            if not self._settings.syzygy_path or not self._settings.enable_tablebase:
                return {
                    "wdl": "unknown",
                    "dtz": None,
                    "dtm": None,
                    "best_move": None,
                    "category": "not_in_tablebase",
                    "pieces": piece_count,
                    "fen": fen,
                }

            async with self._pool.acquire() as engine:
                # Set syzygy path
                engine.update_engine_parameters(
                    {"SyzygyPath": self._settings.syzygy_path}
                )
                engine.set_fen_position(fen)

                # Get best move (will use tablebase if available)
                best_move = engine.get_best_move()
                evaluation = engine.get_evaluation()

                # Determine WDL
                wdl = "unknown"
                if evaluation["type"] == "mate":
                    wdl = "win" if evaluation["value"] > 0 else "loss"
                elif evaluation["type"] == "cp":
                    if abs(evaluation["value"]) < 10:
                        wdl = "draw"
                    elif evaluation["value"] > 0:
                        wdl = "win"
                    else:
                        wdl = "loss"

                return {
                    "wdl": wdl,
                    "dtz": None,
                    "dtm": None,
                    "best_move": best_move,
                    "category": "tablebase",
                    "pieces": piece_count,
                    "fen": fen,
                }

        except Exception as e:
            logger.error(f"Tablebase probe failed: {e}")
            raise StockfishError(f"Tablebase probe failed: {e}")


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
