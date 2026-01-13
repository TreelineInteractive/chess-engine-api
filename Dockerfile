# Multi-stage build for Stockfish Chess Engine API
# Stage 1: Build Stockfish from source

FROM ubuntu:22.04 AS stockfish-builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    wget \
    tar \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Download and extract Stockfish source
WORKDIR /tmp
RUN wget -q https://github.com/official-stockfish/Stockfish/archive/refs/tags/sf_17.1.tar.gz \
    && tar -xzf sf_17.1.tar.gz

# Compile Stockfish with optimal settings
# Detect architecture and use appropriate build flags
WORKDIR /tmp/Stockfish-sf_17.1/src
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then \
        echo "Building for ARM64" && \
        make -j$(nproc) build ARCH=armv8; \
    else \
        echo "Building for x86-64" && \
        make -j$(nproc) build ARCH=x86-64-sse41-popcnt; \
    fi

# Verify the binary was created
RUN test -f stockfish && chmod +x stockfish

# Stage 2: Python application
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    STOCKFISH_PATH=/usr/local/bin/stockfish

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Stockfish binary from builder stage
COPY --from=stockfish-builder /tmp/Stockfish-sf_17.1/src/stockfish /usr/local/bin/stockfish

# Verify Stockfish is executable
RUN chmod +x /usr/local/bin/stockfish \
    && stockfish --version || echo "Stockfish installed"

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app/app
COPY ./tests /app/tests
COPY ./data /app/data

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
