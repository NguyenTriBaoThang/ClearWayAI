"""Configuration module for ClearWayAI API."""

import os

from pydantic import BaseModel, Field

# Simple .env parser to avoid external dependencies
env_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"
)
if os.path.exists(env_path):
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = val


class Settings(BaseModel):
    """Application settings with environment variable fallbacks."""

    APP_NAME: str = Field(default_factory=lambda: os.getenv("APP_NAME", "ClearWayAI API"))
    APP_VERSION: str = Field(default_factory=lambda: os.getenv("APP_VERSION", "0.1.0"))
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    LOG_LEVEL: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "info"))

    # Operational safety modes: SIMULATION | OFFLINE_VIDEO | SHADOW_ADVISORY | AUTHORIZED_PILOT
    # STRICT SAFETY RULE: Default is always SIMULATION with SIMULATION_ONLY=True
    SAFETY_MODE: str = Field(default_factory=lambda: os.getenv("SAFETY_MODE", "SIMULATION"))
    SIMULATION_ONLY: bool = Field(
        default_factory=lambda: os.getenv("SIMULATION_ONLY", "true").lower() == "true"
    )

    # Data Provenance: DEMO_FIXTURE | SUMO_SIMULATED | OFFLINE_VIDEO | LIVE_CONNECTED
    DATA_PROVENANCE: str = Field(
        default_factory=lambda: os.getenv("DATA_PROVENANCE", "DEMO_FIXTURE")
    )
    DEMO_MODE: bool = Field(
        default_factory=lambda: os.getenv("DEMO_MODE", "true").lower() == "true"
    )

    # Server settings
    API_HOST: str = Field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    API_PORT: int = Field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]


settings = Settings()
