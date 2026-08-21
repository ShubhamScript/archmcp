"""
ArchMCP - Token Verifier.

@author Shubham Upadhyay
@license MIT
"""

from typing import Optional
from ..config.settings import settings
from .models import AuthUser


class TokenVerifier:
    """
    Validates incoming API tokens / bearer tokens against settings.valid_tokens.
    """

    @staticmethod
    def verify(token: Optional[str]) -> Optional[AuthUser]:
        """
        Validates a bearer or query token against configured valid tokens.

        @param Optional[str] token: Raw token string from request header or query
        @return Optional[AuthUser]: Validated user entity or None if unauthorized
        """
        if not settings.AUTH_ENABLED:
            return AuthUser(token="anonymous-auth-disabled", username="guest")

        if not token:
            return None

        # Clean token format (strip "Bearer " if sent in HTTP Authorization header)
        clean_token = token.strip()
        if clean_token.lower().startswith("bearer "):
            clean_token = clean_token[7:].strip()

        # Check membership in allowed tokens list
        if clean_token in settings.valid_tokens:
            return AuthUser(token=clean_token, username=f"user-{clean_token[:6]}")

        return None
