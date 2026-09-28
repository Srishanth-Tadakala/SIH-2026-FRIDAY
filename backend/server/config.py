"""Centralized, Strongly-Typed Configuration Layer for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

from functools import lru_cache
import os
from typing import Any, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Platform configuration settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Environment & Server
    ENVIRONMENT: str = Field(default="development", description="Environment mode: development, testing, production")
    SERVER_HOST: str = Field(default="0.0.0.0", description="Bind host address")
    SERVER_PORT: int = Field(default=8000, description="Bind port")
    DEBUG: bool = Field(default=False, description="Debug mode")

    # Security & Authentication
    JWT_SECRET_KEY: str = Field(
        default="friday-antarctica-secret-key-development-mode-2026",
        description="Cryptographic secret key for signing JWT bearer tokens",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, description="Access token expiration in minutes (24h)")

    # Station Commander Safety Interlock PIN & Rate-Limiting
    COMMANDER_PIN: str = Field(
        default="BHARATI-CMD-2026",
        description="Primary Station Commander authorization PIN",
    )
    COMMANDER_LOCKOUT_ATTEMPTS: int = Field(default=5, description="Failed attempts before exponential lockout")
    COMMANDER_LOCKOUT_SECONDS: float = Field(default=300.0, description="Initial lockout cooldown duration")

    # CORS Allowed Origins
    CORS_ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        description="Explicit allowed origins for CORS validation",
    )

    # Groq AI Cognitive Engine
    GROQ_API_KEY: str = Field(default="", description="API key for Groq Cloud LLM engine")
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile", description="Model identifier")
    GROQ_TIMEOUT_SECONDS: float = Field(default=12.0, description="HTTP timeout for LLM inferences")
    GROQ_CIRCUIT_BREAKER_MAX_FAILURES: int = Field(default=3, description="Consecutive errors to trip circuit breaker")
    GROQ_CIRCUIT_BREAKER_RESET_SECONDS: float = Field(default=60.0, description="Cool-off time before half-open state")

    # Persistence Subsystems
    MONGODB_URI: str = Field(default="mongodb://localhost:27017", description="MongoDB connection URI")
    MONGODB_DB_NAME: str = Field(default="friday_antarctic_twin", description="MongoDB database name")
    EDGE_STORAGE_PATH: str = Field(
        default="data/edge_storage/friday_embedded_edge.json",
        description="Local fallback JSON document store path",
    )

    # Satcom & Telemetry
    SATCOM_BANDWIDTH_LIMIT_BPS: int = Field(default=2400, description="Simulated Iridium polar satcom bandwidth limit")
    RATE_LIMIT_PER_MINUTE: int = Field(default=120, description="General API rate limit per client")
    WS_MAX_CONNECTIONS: int = Field(default=100, description="Maximum concurrent WebSocket client connections")
    WS_MAX_PER_IP: int = Field(default=10, description="Maximum concurrent WebSocket connections per IP")
    WS_CLIENT_QUEUE_SIZE: int = Field(default=100, description="Bounded queue depth per WebSocket subscriber")

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret_in_production(cls, v: str, info: Any) -> str:
        # If in production mode, disallow default weak key
        env = os.environ.get("ENVIRONMENT", "development").lower()
        if env == "production":
            if v == "friday-antarctica-secret-key-development-mode-2026" or len(v) < 32:
                raise ValueError("In production mode, JWT_SECRET_KEY must be a unique key with at least 32 characters.")
        return v

    @field_validator("COMMANDER_PIN")
    @classmethod
    def validate_commander_pin_in_production(cls, v: str, info: Any) -> str:
        env = os.environ.get("ENVIRONMENT", "development").lower()
        if env == "production":
            if v == "BHARATI-CMD-2026" or len(v) < 8:
                raise ValueError("In production mode, COMMANDER_PIN must be customized with at least 8 characters.")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached singleton application settings."""
    return Settings()
