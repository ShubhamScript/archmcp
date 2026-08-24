"""
ArchMCP - Enterprise Configuration & Environment Settings.

@author Shubham Upadhyay
@license MIT
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Enterprise application configuration loaded from environment variables or .env file."""
    
    APP_NAME: str = "ArchMCP Server"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Security & Authentication
    AUTH_ENABLED: bool = True
    KEY_STORE_FILE: str = "data/keystore.json"
    BOOTSTRAP_ADMIN_KEY: bool = True

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Structured Security Audit Logging
    AUDIT_LOG_FILE: str = "data/audit.log"

    # Enterprise OIDC / OAuth2 Integration
    OIDC_ENABLED: bool = False
    OIDC_ISSUER: Optional[str] = None
    OIDC_AUDIENCE: Optional[str] = None

    # Storage & Catalogs
    REPOSITORIES_FILE: str = "data/repositories.yaml"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
