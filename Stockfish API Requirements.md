# Stockfish Chess Engine REST API - Software Design & Requirements

## Project Overview
Build a production-ready REST API service that wraps the Stockfish chess engine, containerized with Docker, using FastAPI. The service should expose all major Stockfish features through HTTP endpoints with architecture that allows future WebSocket enhancement for real-time streaming analysis.

## Core Requirements

### Technology Stack
- **Framework**: FastAPI (Python 3.11+)
- **Chess Engine**: Stockfish 17.1 (latest stable)
- **Chess Library**: python-chess (for move validation and board state)
- **Stockfish Wrapper**: stockfish Python library
- **Containerization**: Docker with multi-stage build
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

### Deployment Target
- AWS ECS Fargate compatible
- Horizontal scaling support
- Stateless architecture (no session persistence required)

## API Endpoints

### 1. Best Move Analysis
**Endpoint**: `POST /api/v1/best-move`

**Request Body**:
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "depth": 15,
  "skill_level": 20,
  "time_limit_ms": 1000
}
```

**Response**:
```json
{
  "best_move": "e2e4",
  "evaluation": {
    "type": "cp",
    "value": 25
  },
  "depth": 15,
  "pv_line": ["e2e4", "e7e5", "g1f3"],
  "time_taken_ms": 842
}
```

**Features**:
- Return best move in UCI notation
- Include centipawn evaluation or mate score
- Return principal variation (best continuation line)
- Support depth and time limit parameters
- Support skill level (0-20 for different strength levels)

### 2. Position Evaluation
**Endpoint**: `POST /api/v1/evaluate`

**Request Body**:
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "depth": 15
}
```

**Response**:
```json
{
  "evaluation": {
    "type": "cp",
    "value": 35
  },
  "mate_in": null,
  "depth": 15,
  "best_move": "e7e5",
  "winning_chances": {
    "white": 54.2,
    "black": 45.8
  }
}
```

**Features**:
- Return evaluation in centipawns
- Detect forced mate sequences (mate in N)
- Calculate winning chances percentage using Lichess formula
- Support custom evaluation depth

### 3. Multi-PV Analysis
**Endpoint**: `POST /api/v1/multi-pv`

**Request Body**:
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "depth": 15,
  "num_lines": 3
}
```

**Response**:
```json
{
  "variations": [
    {
      "move": "e2e4",
      "evaluation": {"type": "cp", "value": 25},
      "pv_line": ["e2e4", "e7e5", "g1f3"]
    },
    {
      "move": "d2d4",
      "evaluation": {"type": "cp", "value": 20},
      "pv_line": ["d2d4", "d7d5", "c2c4"]
    },
    {
      "move": "g1f3",
      "evaluation": {"type": "cp", "value": 18},
      "pv_line": ["g1f3", "g8f6", "c2c4"]
    }
  ],
  "depth": 15
}
```

**Features**:
- Return top N best moves (typically 3-5)
- Include evaluation and continuation for each line
- Support configurable number of lines (1-5)

### 4. Move Validation
**Endpoint**: `POST /api/v1/validate-move`

**Request Body**:
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "move": "e2e4"
}
```

**Response**:
```json
{
  "valid": true,
  "san": "e4",
  "resulting_fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "move_type": {
    "is_capture": false,
    "is_castling": false,
    "is_promotion": false,
    "is_check": false,
    "is_checkmate": false
  }
}
```

**Features**:
- Validate move legality
- Convert UCI to SAN notation
- Return resulting FEN after move
- Classify move type (capture, castle, promotion, check, checkmate)

### 5. Legal Moves
**Endpoint**: `POST /api/v1/legal-moves`

**Request Body**:
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "square": "e2"
}
```

**Response**:
```json
{
  "legal_moves": [
    {
      "uci": "e2e3",
      "san": "e3",
      "to_square": "e3"
    },
    {
      "uci": "e2e4",
      "san": "e4",
      "to_square": "e4"
    }
  ],
  "piece": "P",
  "total_moves": 2
}
```

**Features**:
- Return all legal moves for a given position
- Optional: filter by specific piece/square
- Include both UCI and SAN notation

### 6. Position Analysis (Detailed)
**Endpoint**: `POST /api/v1/analyze`

**Request Body**:
```json
{
  "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
  "depth": 18
}
```

**Response**:
```json
{
  "evaluation": {"type": "cp", "value": 45},
  "best_move": "d2d3",
  "threats": ["Nxe4", "Nd4"],
  "tactical_themes": ["pin", "fork_threat"],
  "position_type": "open",
  "material_balance": {
    "white": 39,
    "black": 39,
    "difference": 0
  }
}
```

**Features**:
- Deep position analysis
- Identify tactical themes (pins, forks, skewers)
- Material count
- Position classification (open, closed, tactical)

### 7. Game Analysis (Full Game)
**Endpoint**: `POST /api/v1/analyze-game`

**Request Body**:
```json
{
  "moves": ["e2e4", "e7e5", "g1f3", "b8c6"],
  "starting_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "depth": 15
}
```

**Response**:
```json
{
  "analysis": [
    {
      "move_number": 1,
      "move": "e2e4",
      "evaluation_before": {"type": "cp", "value": 20},
      "evaluation_after": {"type": "cp", "value": 25},
      "best_move": "e2e4",
      "is_best": true,
      "classification": "excellent"
    },
    {
      "move_number": 2,
      "move": "e7e5",
      "evaluation_before": {"type": "cp", "value": -25},
      "evaluation_after": {"type": "cp", "value": -25},
      "best_move": "e7e5",
      "is_best": true,
      "classification": "book"
    }
  ],
  "summary": {
    "total_moves": 4,
    "accuracy": {
      "white": 98.5,
      "black": 97.2
    },
    "mistakes": 0,
    "blunders": 0,
    "excellent_moves": 2,
    "good_moves": 2
  }
}
```

**Features**:
- Analyze complete games move by move
- Classify moves (excellent, good, inaccuracy, mistake, blunder)
- Calculate player accuracy
- Identify critical moments in the game

### 8. FEN Validation
**Endpoint**: `POST /api/v1/validate-fen`

**Request Body**:
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
}
```

**Response**:
```json
{
  "valid": true,
  "errors": [],
  "position_info": {
    "to_move": "white",
    "castling_rights": "KQkq",
    "en_passant": null,
    "halfmove_clock": 0,
    "fullmove_number": 1
  }
}
```

### 9. Engine Info
**Endpoint**: `GET /api/v1/engine/info`

**Response**:
```json
{
  "engine": "Stockfish 17.1",
  "supported_features": [
    "NNUE",
    "MultiPV",
    "Chess960",
    "WDL"
  ],
  "default_parameters": {
    "threads": 1,
    "hash": 128,
    "skill_level": 20
  }
}
```

### 10. Health Check
**Endpoint**: `GET /api/v1/health`

**Response**:
```json
{
  "status": "healthy",
  "engine_available": true,
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

## Future WebSocket Support Architecture

### Design Considerations
The current REST API should be architected to easily support WebSocket streaming in the future without major refactoring.

### Suggested WebSocket Endpoint (Future)
**Endpoint**: `WS /api/v1/ws/analyze-stream`

**Message Format (Client → Server)**:
```json
{
  "action": "analyze",
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "max_depth": 25,
  "time_limit_ms": 5000
}
```

**Message Format (Server → Client)**:
```json
{
  "type": "depth_update",
  "depth": 12,
  "evaluation": {"type": "cp", "value": 25},
  "best_move": "e2e4",
  "pv_line": ["e2e4", "e7e5"],
  "nodes": 120000,
  "nps": 400000
}
```

**Architecture Notes**:
- Use async task queue for long-running analysis
- Allow cancellation of analysis via WebSocket message
- Stream depth updates as engine computes
- Support multiple concurrent WebSocket connections

## Engine Configuration

### Stockfish Parameters
Support configuration of key Stockfish UCI options:

```python
{
  "Threads": 1,              # CPU threads (1-512)
  "Hash": 128,               # Hash table size in MB (1-131072)
  "Ponder": False,           # Think during opponent's time
  "MultiPV": 1,              # Number of principal variations (1-500)
  "Skill Level": 20,         # Playing strength (0-20)
  "Move Overhead": 10,       # Time buffer in ms
  "Minimum Thinking Time": 20,  # Min ms to think
  "UCI_Chess960": False,     # Support Chess960
  "UCI_LimitStrength": False,  # Limit engine strength
  "UCI_Elo": 1350           # Target Elo when limiting strength
}
```

### Environment Variables
```
STOCKFISH_THREADS=1
STOCKFISH_HASH_SIZE_MB=128
STOCKFISH_SKILL_LEVEL=20
MAX_DEPTH=25
DEFAULT_DEPTH=15
MAX_ANALYSIS_TIME_MS=10000
API_RATE_LIMIT_PER_MINUTE=100
```

## Docker Configuration

### Dockerfile Requirements
```dockerfile
# Multi-stage build
# Stage 1: Download and compile Stockfish
FROM ubuntu:22.04 as stockfish-builder

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Download Stockfish source
WORKDIR /tmp
RUN wget https://github.com/official-stockfish/Stockfish/archive/refs/tags/sf_17.1.tar.gz \
    && tar -xzf sf_17.1.tar.gz

# Compile Stockfish (use optimal arch for target platform)
WORKDIR /tmp/Stockfish-sf_17.1/src
RUN make -j build ARCH=x86-64-modern

# Stage 2: Application
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy Stockfish binary from builder
COPY --from=stockfish-builder /tmp/Stockfish-sf_17.1/src/stockfish /usr/local/bin/stockfish

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### Docker Compose (Development)
```yaml
version: '3.8'

services:
  stockfish-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - STOCKFISH_THREADS=2
      - STOCKFISH_HASH_SIZE_MB=256
      - MAX_DEPTH=25
      - DEFAULT_DEPTH=15
    volumes:
      - ./app:/app
    restart: unless-stopped
```

## Code Structure

```
stockfish-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py               # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py         # Pydantic request models
│   │   └── responses.py        # Pydantic response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── stockfish_service.py  # Stockfish engine wrapper
│   │   └── analysis_service.py   # High-level analysis logic
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── analysis.py         # Analysis endpoints
│   │   ├── moves.py            # Move-related endpoints
│   │   └── engine.py           # Engine info endpoints
│   └── utils/
│       ├── __init__.py
│       ├── chess_utils.py      # Chess helper functions
│       └── validators.py       # Input validation
├── tests/
│   ├── __init__.py
│   ├── test_analysis.py
│   ├── test_moves.py
│   └── test_engine.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Dependencies (requirements.txt)

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-chess==1.999
stockfish==3.28.0
pydantic==2.5.3
python-dotenv==1.0.0
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
```

## Error Handling

### Standard Error Response Format
```json
{
  "error": {
    "code": "INVALID_FEN",
    "message": "The provided FEN string is invalid",
    "details": "Missing piece placement data"
  }
}
```

### Error Codes
- `INVALID_FEN`: FEN string syntax error
- `INVALID_MOVE`: Move is not legal in position
- `ENGINE_ERROR`: Stockfish engine error
- `TIMEOUT`: Analysis exceeded time limit
- `INVALID_DEPTH`: Depth parameter out of range
- `RATE_LIMIT_EXCEEDED`: Too many requests

## Performance Requirements

### Response Times (Target)
- Simple move validation: < 50ms
- Best move calculation (depth 15): < 1000ms
- Position evaluation: < 1000ms
- Multi-PV analysis (3 lines): < 2000ms
- Full game analysis: < 5000ms (50 moves)

### Concurrency
- Support at least 10 concurrent requests per container
- Implement connection pooling for Stockfish instances
- Use async/await for non-blocking I/O

### Resource Limits
- Max depth: 25 (configurable)
- Max analysis time: 10 seconds (configurable)
- Memory limit per container: 512MB-1GB
- CPU: 1-2 vCPUs per container

## Security Considerations

### Input Validation
- Validate all FEN strings before passing to engine
- Sanitize move strings
- Limit request payload size (< 1MB)
- Rate limiting per IP address

### API Security
- CORS configuration for allowed origins
- API key authentication (optional)
- Request logging for monitoring
- No sensitive data exposure in error messages

## Testing Requirements

### Unit Tests
- Test all endpoint handlers
- Test Stockfish service wrapper
- Test chess utility functions
- Test input validation

### Integration Tests
- Test full API workflows
- Test error handling
- Test concurrent requests
- Test Docker container

### Test Coverage Target
- Minimum 80% code coverage
- 100% coverage on critical paths (move validation, engine interface)

## Documentation Requirements

### API Documentation
- Auto-generated OpenAPI/Swagger docs
- Example requests and responses for each endpoint
- Authentication guide (if applicable)
- Rate limiting documentation

### Deployment Documentation
- Docker build and run instructions
- Environment variable configuration
- AWS ECS deployment guide
- Performance tuning recommendations

## Monitoring & Logging

### Logging Requirements
- Structured JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log request/response times
- Log engine parameters for each request

### Metrics to Track
- Request count by endpoint
- Average response time by endpoint
- Error rate
- Engine analysis depth achieved
- Concurrent connections

### Log Format Example
```json
{
  "timestamp": "2025-01-13T12:00:00Z",
  "level": "INFO",
  "endpoint": "/api/v1/best-move",
  "method": "POST",
  "status_code": 200,
  "response_time_ms": 842,
  "depth": 15,
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
}
```

## Deployment Considerations

### AWS ECS Fargate
- Task definition with 1 vCPU, 1GB memory
- Health check endpoint configured
- Auto-scaling based on CPU utilization (>70%)
- Application Load Balancer for traffic distribution
- CloudWatch logs integration

### Environment-Specific Configuration
- Development: Lower resource limits, verbose logging
- Staging: Production-like setup with test data
- Production: Optimized performance, INFO-level logging

## Future Enhancements (Phase 2)

1. **WebSocket Streaming**: Real-time analysis updates as depth increases
2. **Opening Book Integration**: Detect opening names and variations
3. **Endgame Tablebase**: Syzygy tablebase support for perfect endgame play
4. **Game Database**: Store and retrieve analyzed games
5. **Puzzle Generation**: Generate tactical puzzles from positions
6. **Training Mode**: Adaptive difficulty based on player strength
7. **Multi-Engine Support**: Add support for other UCI engines (Leela, etc.)
8. **Cloud PGN Import**: Analyze games from Lichess/Chess.com via API

## Success Criteria

### Functional Requirements Met
- ✅ All 10 REST endpoints implemented and tested
- ✅ Docker container builds successfully
- ✅ Stockfish 17.1 integrated and responding
- ✅ Input validation working correctly
- ✅ Error handling comprehensive

### Non-Functional Requirements Met
- ✅ Average response time < 1 second for depth 15
- ✅ 80%+ test coverage
- ✅ API documentation complete
- ✅ Successfully deploys to ECS Fargate
- ✅ Handles 10+ concurrent requests

## License Compliance

### Stockfish GPL v3
- Include full GPL v3 license text in repository
- Document that Stockfish is licensed under GPL v3
- Link to Stockfish source code repository
- Comply with GPL requirements for distribution

### Application Code
- Application wrapper code can remain closed-source
- Only the Stockfish binary itself requires GPL compliance
- Document which components are GPL vs proprietary

---

## Implementation Notes for AI Agent

This specification provides a complete blueprint for building a production-ready Stockfish REST API. The architecture is designed to be:

1. **Stateless**: Each request is independent, allowing horizontal scaling
2. **Performant**: Async/await patterns and efficient engine usage
3. **Extensible**: Easy to add WebSocket support in Phase 2
4. **Production-Ready**: Proper error handling, logging, and monitoring
5. **Well-Tested**: Comprehensive test coverage requirements
6. **Cloud-Native**: Docker containerized and ECS-ready

The AI agent should prioritize:
- Clean, readable code with type hints
- Comprehensive error handling
- Efficient resource usage (engine pooling)
- Clear separation of concerns (services, routers, models)
- Thorough documentation and examples

Start with core endpoints (best-move, evaluate, validate-move) and build out from there. Ensure each component is tested before moving to the next.
