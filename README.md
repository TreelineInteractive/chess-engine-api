# Stockfish Chess Engine REST API

A production-ready REST API service that wraps the Stockfish chess engine, providing comprehensive chess analysis capabilities through HTTP endpoints.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg)](https://fastapi.tiangolo.com)
[![Stockfish 17.1](https://img.shields.io/badge/Stockfish-17.1-darkgreen.svg)](https://stockfishchess.org/)

## Features

- 🎯 **Best Move Analysis** - Get optimal moves with evaluation scores
- 📊 **Position Evaluation** - Centipawn and mate score evaluations
- 🔀 **Multi-PV Analysis** - Multiple best lines for a position
- ✅ **Move Validation** - Validate moves with detailed information
- 📝 **Legal Moves** - List all legal moves for any position
- 🎮 **Game Analysis** - Analyze complete games with accuracy scores
- 🔍 **FEN Validation** - Validate FEN strings with error details
- 📈 **WDL Statistics** - Win/Draw/Loss probabilities using Lichess formula
- 📚 **Opening Book** - 3,630+ openings from Lichess with ECO codes, variations, and popularity ratings
- ⚡ **Perft Testing** - Performance testing for move generation
- 🏆 **Benchmarking** - Engine performance measurement
- ⚙️ **Engine Configuration** - Runtime UCI parameter updates
- 🎲 **Tablebase Support** - Syzygy endgame tablebase probing
- 🔐 **Optional Authentication** - JWT/JWKS support for Supabase and other providers
- 🏗️ **Production Ready** - Docker containerized, horizontally scalable
- 📚 **Auto Documentation** - OpenAPI/Swagger docs included
- 🚀 **High Performance** - Async I/O, connection pooling

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, recommended)

### Running with Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd chess-engine-api
```

2. Build and run with Docker Compose:
```bash
docker compose up --build
```

3. **Configure authentication** (optional):
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your authentication settings
# See AUTHENTICATION.md for detailed setup instructions
# AUTH_ENABLED=true
# JWKS_URL=https://your-project.supabase.co/auth/v1/.well-known/jwks.json
# JWT_AUDIENCE=authenticated

# Run with your configuration
docker compose up
```

4. Access the API:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

### Running Locally (Development)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Download Stockfish:
```bash
# macOS
brew install stockfish

# Ubuntu/Debian
sudo apt-get install stockfish

# Or download from https://stockfishchess.org/download/
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env and set STOCKFISH_PATH to your Stockfish binary location
```

4. Run the application:
```bash
cd app
uvicorn main:app --reload
```

## API Endpoints

### Analysis Endpoints

#### POST `/api/v1/best-move`
Get the best move for a chess position.

**Request:**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "depth": 15,
  "skill_level": 20,
  "time_limit_ms": 1000
}
```

**Response:**
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

#### POST `/api/v1/evaluate`
Evaluate a chess position.

**Request:**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "depth": 15
}
```

**Response:**
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

#### POST `/api/v1/multi-pv`
Get multiple best lines for a position.

**Request:**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "depth": 15,
  "num_lines": 3
}
```

#### POST `/api/v1/analyze`
Detailed position analysis with tactical themes.

**Request:**
```json
{
  "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
  "depth": 18
}
```

#### POST `/api/v1/analyze-game`
Analyze a complete chess game move by move.

**Request:**
```json
{
  "moves": ["e2e4", "e7e5", "g1f3", "b8c6"],
  "starting_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "depth": 15
}
```

#### POST `/api/v1/wdl-stats`
Calculate Win/Draw/Loss probabilities for a position using the Lichess formula.

**Request:**
```json
{
  "fen": "startpos",
  "depth": 15
}
```

**Response:**
```json
{
  "wdl": {
    "win": 40.7,
    "draw": 22.9,
    "loss": 36.4
  },
  "evaluation": {
    "type": "cp",
    "value": 30
  },
  "depth": 15,
  "model": "Lichess formula",
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "time_ms": 1563
}
```

#### POST `/api/v1/opening-book`
Identify chess opening name, ECO code, and theory for a sequence of moves.

**Request:**
```json
{
  "moves": ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"]
}
```

**Response:**
```json
{
  "opening_name": "Italian Game",
  "eco": "C50",
  "variation": "Giuoco Piano",
  "popularity": "very common",
  "theory_moves": ["f8c5", "g8f6"],
  "known_until_move": 5,
  "in_book": true,
  "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
}
```

### Move Endpoints

#### POST `/api/v1/validate-move`
Validate a chess move.

**Request:**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "move": "e2e4"
}
```

**Response:**
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

#### POST `/api/v1/legal-moves`
Get all legal moves for a position.

**Request:**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "square": "e2"
}
```

#### POST `/api/v1/validate-fen`
Validate a FEN string.

**Request:**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
}
```

### Engine Endpoints

#### GET `/api/v1/engine/info`
Get Stockfish engine information.

**Response:**
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

#### GET `/api/v1/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "engine_available": true,
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

#### POST `/api/v1/perft`
Run performance test (perft) to count all possible positions from a given position.

**Request:**
```json
{
  "fen": "startpos",
  "depth": 5,
  "divide": false
}
```

**Response:**
```json
{
  "nodes": 4865609,
  "depth": 5,
  "time_ms": 14507,
  "nps": 335397,
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "divide": null
}
```

#### GET `/api/v1/benchmark`
Run the built-in Stockfish benchmark to measure engine performance.

**Response:**
```json
{
  "total_nodes": 2030154,
  "nodes_per_second": 446285,
  "time_ms": 4549,
  "positions_tested": 50,
  "depth": 13,
  "threads": 2,
  "hash_mb": 256,
  "signature": "2030154"
}
```

#### POST `/api/v1/engine/configure`
Update Stockfish UCI engine parameters.

**Request:**
```json
{
  "threads": 4,
  "hash_mb": 512,
  "skill_level": 20
}
```

**Response:**
```json
{
  "updated_parameters": {
    "threads": 4,
    "hash_mb": 512
  },
  "current_configuration": {
    "threads": 4,
    "hash_mb": 512,
    "skill_level": 20,
    "ponder": false,
    "multi_pv": 1
  },
  "restart_required": false
}
```

### Tablebase Endpoints

#### POST `/api/v1/tablebase-probe`
Query Syzygy endgame tablebases for perfect play in endgame positions.

**Request:**
```json
{
  "fen": "8/8/8/8/8/1k6/8/K7 w - - 0 1"
}
```

**Response:**
```json
{
  "wdl": "draw",
  "dtz": 0,
  "in_tablebase": true,
  "fen": "8/8/8/8/8/1k6/8/K7 w - - 0 1"
}
```

## Configuration

Environment variables (see `.env.example`):

```bash
# Stockfish Configuration
STOCKFISH_PATH=/usr/local/bin/stockfish
STOCKFISH_THREADS=1
STOCKFISH_HASH_SIZE_MB=128
STOCKFISH_SKILL_LEVEL=20

# Analysis Configuration
MAX_DEPTH=25
DEFAULT_DEPTH=15
MAX_ANALYSIS_TIME_MS=10000
MAX_MULTI_PV=5

# API Configuration
API_VERSION=1.0.0
API_RATE_LIMIT_PER_MINUTE=100
MAX_CONCURRENT_ANALYSES=10

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=1
DEBUG=false

# CORS Configuration
CORS_ORIGINS=*

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Advanced Features Configuration
SYZYGY_PATH=              # Path to Syzygy tablebase files (leave empty if not using)
MAX_PERFT_DEPTH=6         # Maximum perft depth (1-7)
BENCHMARK_TIMEOUT_SECONDS=60
```

## Authentication (Optional)

The API supports optional JWT authentication using JWKS (JSON Web Key Set) for token validation. This is disabled by default to keep the API open for public use, but can be enabled for production deployments requiring user authentication.

**📖 For detailed authentication setup, testing, and integration instructions, see [AUTHENTICATION.md](./AUTHENTICATION.md)**

### Quick Setup

#### Supabase
```bash
AUTH_ENABLED=true
JWKS_URL=https://your-project.supabase.co/auth/v1/.well-known/jwks.json
JWT_AUDIENCE=authenticated
```

#### Auth0
```bash
AUTH_ENABLED=true
JWKS_URL=https://your-domain.auth0.com/.well-known/jwks.json
JWT_AUDIENCE=your-api-identifier
```

### Protected Endpoints

When `AUTH_ENABLED=true`, all endpoints require a valid JWT token except:
- `GET /api/v1/health` - Health check
- `GET /api/v1/ready` - Readiness check

Include the JWT token in requests:
```bash
curl -X POST https://api.example.com/api/v1/best-move \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fen": "startpos", "depth": 15}'
```

@router.post("/best-move")
async def get_best_move(
    request: BestMoveRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
    user: Annotated[Optional[dict], Depends(get_current_user)] = None,
) -> BestMoveResponse:
    # When AUTH_ENABLED=false: user is None (no auth required)
    # When AUTH_ENABLED=true: user contains JWT claims or raises 401
    # You can optionally use user data for logging, rate limiting, etc.
    return await service.get_best_move(...)
```

**Behavior:**
- **AUTH_ENABLED=false**: User can access all endpoints without tokens, `user` parameter is None
- **AUTH_ENABLED=true**: All endpoints require valid JWT token, `user` contains claims (sub, email, etc.), invalid/missing tokens return 401

## Deployment

For complete deployment guides including AWS App Runner (current setup), Docker Compose, and other cloud platforms, see:
- **[AUTHENTICATION.md](./AUTHENTICATION.md)** - JWT authentication setup and testing
- **[DEPLOYMENT-SETUP.md](./DEPLOYMENT-SETUP.md)** - AWS App Runner setup (current workflow)
- **[ENV_SETUP.md](./ENV_SETUP.md)** - Quick environment variable reference

## Docker Deployment

### Build the Image

```bash
docker build -t stockfish-api:latest .
```

### Run the Container

```bash
docker run -d \
  --name stockfish-api \
  -p 8000:8000 \
  -e STOCKFISH_THREADS=2 \
  -e STOCKFISH_HASH_SIZE_MB=256 \
  stockfish-api:latest
```

### Docker Compose (Production)

```bash
docker compose up -d
```

### Docker Compose (Development with Hot Reload)

```bash
docker compose --profile dev up
```

## AWS ECS Deployment

### Task Definition

```json
{
  "family": "stockfish-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "stockfish-api",
      "image": "your-ecr-repo/stockfish-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "STOCKFISH_THREADS",
          "value": "2"
        },
        {
          "name": "STOCKFISH_HASH_SIZE_MB",
          "value": "512"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/api/v1/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 10
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/stockfish-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_analysis.py

# Run with verbose output
pytest -v
```

Test coverage target: **80%+**

## Performance

### Benchmarks

- Best move (depth 15): < 1000ms
- Position evaluation: < 1000ms
- Multi-PV (3 lines): < 2000ms
- Move validation: < 50ms
- Full game analysis (50 moves): < 5000ms

### Scaling

- Supports 10+ concurrent requests per container
- Horizontally scalable (stateless design)
- Connection pooling for efficient resource usage
- Async I/O for non-blocking operations

## API Rate Limiting

Default rate limit: **100 requests/minute per IP**

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1234567890
```

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional details (optional)"
  }
}
```

### Error Codes

- `INVALID_FEN` - FEN string syntax error
- `INVALID_MOVE` - Move is not legal in position
- `ENGINE_ERROR` - Stockfish engine error
- `TIMEOUT` - Analysis exceeded time limit
- `INVALID_DEPTH` - Depth parameter out of range
- `RATE_LIMIT_EXCEEDED` - Too many requests

## Logging

Structured JSON logging for production:

```json
{
  "timestamp": "2025-01-13T12:00:00Z",
  "level": "INFO",
  "endpoint": "/api/v1/best-move",
  "method": "POST",
  "status_code": 200,
  "response_time_ms": 842,
  "depth": 15
}
```

## Development

### Project Structure

```
stockfish-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Configuration
│   ├── models/
│   │   ├── requests.py         # Request models
│   │   └── responses.py        # Response models
│   ├── services/
│   │   ├── stockfish_service.py  # Engine wrapper
│   │   └── analysis_service.py   # Analysis logic
│   ├── routers/
│   │   ├── analysis.py         # Analysis endpoints
│   │   ├── moves.py            # Move endpoints
│   │   └── engine.py           # Engine endpoints
│   └── utils/
│       ├── chess_utils.py      # Chess utilities
│       └── validators.py       # Input validation
├── tests/
│   ├── test_analysis.py
│   ├── test_moves.py
│   ├── test_engine.py
│   └── test_utils.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

### Code Quality

- Type hints throughout
- Async/await patterns
- Comprehensive error handling
- Structured logging
- 80%+ test coverage

## License

This project uses **Stockfish**, which is licensed under the GNU General Public License v3.0 (GPL-3.0).

The API wrapper code is also licensed under GPL-3.0 to comply with Stockfish's license requirements.

- [Stockfish License](https://github.com/official-stockfish/Stockfish/blob/master/Copying.txt)
- [GPL-3.0 Full Text](https://www.gnu.org/licenses/gpl-3.0.en.html)

### License Compliance

When using or distributing this software:
- You must include the full GPL-3.0 license text
- Any derivative works must also be GPL-3.0 licensed
- You must provide access to the source code
- Link to the original Stockfish source code repository

## Credits

- **Stockfish** - The world's strongest open-source chess engine
  - Website: https://stockfishchess.org/
  - Source: https://github.com/official-stockfish/Stockfish
- **python-chess** - Python chess library
  - Docs: https://python-chess.readthedocs.io/
- **FastAPI** - Modern Python web framework
  - Website: https://fastapi.tiangolo.com/

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For issues and questions:
- Open an issue on GitHub
- Check the [API documentation](http://localhost:8000/docs)
- Review the [requirements document](Stockfish%20API%20Requirements.md)

## Roadmap

Future enhancements (Phase 2):
- WebSocket streaming for real-time analysis updates
- Opening book integration
- Endgame tablebase (Syzygy) support
- Game database storage
- Puzzle generation
- Multi-engine support (Leela Chess Zero, etc.)

---

**Built with ❤️ using Stockfish and FastAPI**
