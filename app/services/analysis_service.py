"""High-level analysis service using Stockfish."""

import logging
from typing import Any, Optional

import chess

from app.config import Settings, get_settings
from app.models.responses import (
    AccuracyScore,
    AnalyzeGameResponse,
    AnalyzePositionResponse,
    BestMoveResponse,
    EvaluateResponse,
    Evaluation,
    GameSummary,
    LegalMove,
    LegalMovesResponse,
    MoveAnalysis,
    MoveType,
    MultiPVResponse,
    PositionInfo,
    ValidateFenResponse,
    ValidateMoveResponse,
    Variation,
)
from app.services.stockfish_service import StockfishService, get_stockfish_service
from app.utils.chess_utils import (
    calculate_material_balance,
    calculate_winning_chances,
    classify_move,
    classify_position_type,
    detect_tactical_themes,
    get_piece_symbol,
    parse_fen_info,
)
from app.utils.validators import validate_fen, validate_move_uci, validate_square

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    High-level analysis service that combines Stockfish engine
    with chess utilities for comprehensive analysis.
    """
    
    def __init__(self, stockfish_service: StockfishService, settings: Settings):
        self._stockfish = stockfish_service
        self._settings = settings
    
    async def get_best_move(
        self,
        fen: str,
        depth: Optional[int] = None,
        skill_level: Optional[int] = None,
        time_limit_ms: Optional[int] = None,
    ) -> BestMoveResponse:
        """
        Get the best move for a position.
        
        Args:
            fen: FEN string
            depth: Analysis depth
            skill_level: Engine skill level
            time_limit_ms: Time limit in milliseconds
            
        Returns:
            BestMoveResponse with best move and evaluation
        """
        result = await self._stockfish.get_best_move(
            fen=fen,
            depth=depth,
            skill_level=skill_level,
            time_limit_ms=time_limit_ms,
        )
        
        return BestMoveResponse(
            best_move=result.best_move,
            evaluation=result.evaluation,
            depth=result.depth,
            pv_line=result.pv_line,
            time_taken_ms=result.time_ms or 0,
        )
    
    async def evaluate_position(
        self,
        fen: str,
        depth: Optional[int] = None,
    ) -> EvaluateResponse:
        """
        Evaluate a position.
        
        Args:
            fen: FEN string
            depth: Analysis depth
            
        Returns:
            EvaluateResponse with evaluation and winning chances
        """
        result = await self._stockfish.evaluate_position(fen=fen, depth=depth)
        
        winning_chances = calculate_winning_chances(result.evaluation)
        
        return EvaluateResponse(
            evaluation=result.evaluation,
            mate_in=result.mate_in,
            depth=result.depth,
            best_move=result.best_move,
            winning_chances=winning_chances,
        )
    
    async def get_multi_pv(
        self,
        fen: str,
        num_lines: int = 3,
        depth: Optional[int] = None,
    ) -> MultiPVResponse:
        """
        Get multiple best lines for a position.
        
        Args:
            fen: FEN string
            num_lines: Number of lines to return
            depth: Analysis depth
            
        Returns:
            MultiPVResponse with variations
        """
        variations_data = await self._stockfish.get_multi_pv(
            fen=fen,
            num_lines=num_lines,
            depth=depth,
        )
        
        variations = [
            Variation(
                move=v["move"],
                evaluation=v["evaluation"],
                pv_line=v["pv_line"],
            )
            for v in variations_data
        ]
        
        return MultiPVResponse(
            variations=variations,
            depth=depth or self._settings.default_depth,
        )
    
    def validate_move(self, fen: str, move: str) -> ValidateMoveResponse:
        """
        Validate a move and return detailed information.
        
        Args:
            fen: FEN string
            move: Move in UCI notation
            
        Returns:
            ValidateMoveResponse with validation result
        """
        # Validate FEN first
        is_valid_fen, fen_errors, board = validate_fen(fen)
        if not is_valid_fen:
            return ValidateMoveResponse(
                valid=False,
                error=f"Invalid FEN: {', '.join(fen_errors)}",
            )
        
        # Validate move
        is_valid_move, chess_move, move_error = validate_move_uci(move, board)
        
        if not is_valid_move:
            return ValidateMoveResponse(
                valid=False,
                error=move_error,
            )
        
        # Get SAN notation
        san = board.san(chess_move)
        
        # Determine move type before making the move
        is_capture = board.is_capture(chess_move)
        is_castling = board.is_castling(chess_move)
        is_en_passant = board.is_en_passant(chess_move)
        
        # Check for promotion
        is_promotion = chess_move.promotion is not None
        
        # Make the move to check for check/checkmate
        board.push(chess_move)
        is_check = board.is_check()
        is_checkmate = board.is_checkmate()
        resulting_fen = board.fen()
        
        move_type = MoveType(
            is_capture=is_capture,
            is_castling=is_castling,
            is_promotion=is_promotion,
            is_check=is_check,
            is_checkmate=is_checkmate,
            is_en_passant=is_en_passant,
        )
        
        return ValidateMoveResponse(
            valid=True,
            san=san,
            resulting_fen=resulting_fen,
            move_type=move_type,
        )
    
    def get_legal_moves(
        self,
        fen: str,
        square: Optional[str] = None,
    ) -> LegalMovesResponse:
        """
        Get all legal moves for a position.
        
        Args:
            fen: FEN string
            square: Optional square to filter moves for
            
        Returns:
            LegalMovesResponse with list of legal moves
        """
        # Validate FEN
        is_valid, errors, board = validate_fen(fen)
        if not is_valid:
            raise ValueError(f"Invalid FEN: {', '.join(errors)}")
        
        piece_on_square = None
        filter_square = None
        
        # Validate and parse square if provided
        if square:
            is_valid_sq, sq_index, sq_error = validate_square(square)
            if not is_valid_sq:
                raise ValueError(f"Invalid square: {sq_error}")
            filter_square = sq_index
            piece = board.piece_at(filter_square)
            piece_on_square = get_piece_symbol(piece)
        
        legal_moves = []
        for move in board.legal_moves:
            # Filter by square if specified
            if filter_square is not None and move.from_square != filter_square:
                continue
            
            uci = move.uci()
            san = board.san(move)
            to_square = chess.square_name(move.to_square)
            
            legal_moves.append(LegalMove(
                uci=uci,
                san=san,
                to_square=to_square,
            ))
        
        return LegalMovesResponse(
            legal_moves=legal_moves,
            piece=piece_on_square,
            total_moves=len(legal_moves),
        )
    
    async def analyze_position(
        self,
        fen: str,
        depth: Optional[int] = None,
    ) -> AnalyzePositionResponse:
        """
        Perform detailed position analysis.
        
        Args:
            fen: FEN string
            depth: Analysis depth
            
        Returns:
            AnalyzePositionResponse with detailed analysis
        """
        # Get evaluation from engine
        result = await self._stockfish.get_best_move(
            fen=fen,
            depth=depth or 18,  # Use higher depth for detailed analysis
        )
        
        # Parse position
        is_valid, errors, board = validate_fen(fen)
        if not is_valid:
            raise ValueError(f"Invalid FEN: {', '.join(errors)}")
        
        # Calculate material balance
        material = calculate_material_balance(board)
        
        # Classify position type
        position_type = classify_position_type(board)
        
        # Detect tactical themes
        tactical_themes = detect_tactical_themes(board)
        
        # Identify threats (simplified - based on opponent's best response)
        threats = []
        if result.best_move:
            # The "threat" is essentially what we're preventing
            board_copy = board.copy()
            # Check if opponent has dangerous moves
            board_copy.push_uci(result.best_move)
            for move in board_copy.legal_moves:
                if board_copy.is_capture(move) or board_copy.gives_check(move):
                    threats.append(board_copy.san(move))
                    if len(threats) >= 3:
                        break
        
        return AnalyzePositionResponse(
            evaluation=result.evaluation,
            best_move=result.best_move,
            threats=threats,
            tactical_themes=tactical_themes,
            position_type=position_type,
            material_balance=material,
        )
    
    async def analyze_game(
        self,
        moves: list[str],
        starting_fen: str,
        depth: Optional[int] = None,
    ) -> AnalyzeGameResponse:
        """
        Analyze a complete game move by move.
        
        Args:
            moves: List of moves in UCI notation
            starting_fen: Starting position FEN
            depth: Analysis depth for each move
            
        Returns:
            AnalyzeGameResponse with move-by-move analysis
        """
        analysis_depth = depth or 15
        
        # Validate starting FEN
        is_valid, errors, board = validate_fen(starting_fen)
        if not is_valid:
            raise ValueError(f"Invalid starting FEN: {', '.join(errors)}")
        
        move_analyses = []
        
        # Statistics for summary
        white_moves = []
        black_moves = []
        mistakes = 0
        blunders = 0
        inaccuracies = 0
        excellent_moves = 0
        good_moves = 0
        book_moves = 0
        
        for i, move_uci in enumerate(moves):
            move_number = (i // 2) + 1
            is_white_move = (i % 2 == 0)
            
            # Get evaluation before the move
            try:
                eval_before_result = await self._stockfish.get_best_move(
                    fen=board.fen(),
                    depth=analysis_depth,
                )
                eval_before = eval_before_result.evaluation
                best_move = eval_before_result.best_move
            except Exception as e:
                logger.error(f"Error analyzing position before move {i+1}: {e}")
                continue
            
            # Validate and make the move
            is_valid_move, chess_move, move_error = validate_move_uci(move_uci, board)
            if not is_valid_move:
                logger.warning(f"Invalid move {move_uci} at position {i+1}: {move_error}")
                continue
            
            san = board.san(chess_move)
            was_best = (move_uci == best_move)
            
            # Make the move
            board.push(chess_move)
            
            # Get evaluation after the move
            try:
                eval_after_result = await self._stockfish.get_best_move(
                    fen=board.fen(),
                    depth=analysis_depth,
                )
                eval_after = eval_after_result.evaluation
            except Exception as e:
                logger.error(f"Error analyzing position after move {i+1}: {e}")
                # Use inverted before evaluation as approximation
                eval_after = Evaluation(
                    type=eval_before.type,
                    value=-eval_before.value,
                )
            
            # Classify the move
            classification = classify_move(
                eval_before=eval_before,
                eval_after=eval_after,
                was_best_move=was_best,
                is_book_move=(i < 10 and abs(eval_before.value) < 30 if eval_before.type == "cp" else False),
            )
            
            # Update statistics
            if classification == "blunder":
                blunders += 1
            elif classification == "mistake":
                mistakes += 1
            elif classification == "inaccuracy":
                inaccuracies += 1
            elif classification == "excellent":
                excellent_moves += 1
            elif classification == "good":
                good_moves += 1
            elif classification == "book":
                book_moves += 1
            
            # Track accuracy per player
            if is_white_move:
                white_moves.append(classification)
            else:
                black_moves.append(classification)
            
            move_analyses.append(MoveAnalysis(
                move_number=move_number,
                move=move_uci,
                san=san,
                evaluation_before=eval_before,
                evaluation_after=eval_after,
                best_move=best_move,
                is_best=was_best,
                classification=classification,
            ))
        
        # Calculate accuracy using weighted scores
        white_accuracy = self._calculate_accuracy(white_moves)
        black_accuracy = self._calculate_accuracy(black_moves)
        
        summary = GameSummary(
            total_moves=len(moves),
            accuracy=AccuracyScore(white=white_accuracy, black=black_accuracy),
            mistakes=mistakes,
            blunders=blunders,
            inaccuracies=inaccuracies,
            excellent_moves=excellent_moves,
            good_moves=good_moves,
            book_moves=book_moves,
        )
        
        return AnalyzeGameResponse(
            analysis=move_analyses,
            summary=summary,
        )
    
    def _calculate_accuracy(self, move_classifications: list[str]) -> float:
        """
        Calculate accuracy percentage from move classifications.
        
        Uses a weighted scoring system similar to chess.com/lichess.
        """
        if not move_classifications:
            return 100.0
        
        # Scoring weights
        weights = {
            "excellent": 1.0,
            "book": 1.0,
            "good": 0.9,
            "inaccuracy": 0.6,
            "mistake": 0.3,
            "blunder": 0.0,
        }
        
        total_score = sum(
            weights.get(cls, 0.5) for cls in move_classifications
        )
        max_score = len(move_classifications)
        
        return round((total_score / max_score) * 100, 1)
    
    def validate_fen(self, fen: str) -> ValidateFenResponse:
        """
        Validate a FEN string.
        
        Args:
            fen: FEN string to validate
            
        Returns:
            ValidateFenResponse with validation result
        """
        is_valid, errors, board = validate_fen(fen)
        
        if not is_valid:
            return ValidateFenResponse(
                valid=False,
                errors=errors,
                position_info=None,
            )
        
        position_info = parse_fen_info(fen)
        
        return ValidateFenResponse(
            valid=True,
            errors=[],
            position_info=position_info,
        )


# Singleton instance
_analysis_service: Optional[AnalysisService] = None


async def get_analysis_service() -> AnalysisService:
    """Get or create the AnalysisService singleton."""
    global _analysis_service
    
    if _analysis_service is None:
        stockfish_service = await get_stockfish_service()
        settings = get_settings()
        _analysis_service = AnalysisService(stockfish_service, settings)
    
    return _analysis_service
