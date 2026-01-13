"""Configuration management for the Stockfish API."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Stockfish Configuration
    stockfish_path: str = Field(
        default="/usr/local/bin/stockfish",
        description="Path to the Stockfish binary",
    )
    stockfish_threads: int = Field(
        default=1,
        ge=1,
        le=512,
        description="Number of CPU threads for Stockfish",
    )
    stockfish_hash_size_mb: int = Field(
        default=128,
        ge=1,
        le=131072,
        description="Hash table size in MB",
    )
    stockfish_skill_level: int = Field(
        default=20,
        ge=0,
        le=20,
        description="Default skill level (0-20)",
    )

    # Analysis Configuration
    max_depth: int = Field(
        default=25,
        ge=1,
        le=100,
        description="Maximum analysis depth allowed",
    )
    default_depth: int = Field(
        default=15,
        ge=1,
        le=50,
        description="Default analysis depth",
    )
    max_analysis_time_ms: int = Field(
        default=10000,
        ge=100,
        le=60000,
        description="Maximum analysis time in milliseconds",
    )
    max_multi_pv: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of principal variations",
    )

    # API Configuration
    api_version: str = Field(
        default="1.0.0",
        description="API version string",
    )
    api_rate_limit_per_minute: int = Field(
        default=100,
        ge=1,
        description="Rate limit per IP per minute",
    )
    max_concurrent_analyses: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum concurrent analysis requests",
    )

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    workers: int = Field(default=1, ge=1, description="Number of workers")
    debug: bool = Field(default=False, description="Debug mode")

    # CORS Configuration
    cors_origins: str = Field(
        default="*",
        description="Allowed CORS origins (comma-separated)",
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or text)",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return upper_v

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
