"""
ArchMCP - Configuration & Environment Settings.

@author Shubham Upadhyay
@license MIT
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables or .env file."""
    
    APP_NAME: str = "ArchMCP Server"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    AUTH_ENABLED: bool = True
    AUTH_TOKENS: str = "dev-token-secret-123,employee-key-abc"
    REPOSITORIES_FILE: str = "data/repositories.yaml"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def valid_tokens(self) -> List[str]:
        """
        Parses comma-separated AUTH_TOKENS string into a list.

        @return List[str]: List of valid authentication token strings
        """
        return [t.strip() for t in self.AUTH_TOKENS.split(",") if t.strip()]


settings = Settings()
