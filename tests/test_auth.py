"""Tests for authentication and token verification in ArchMCP."""

from archmcp.auth.token_verifier import TokenVerifier
from archmcp.config.settings import settings


def test_valid_token_verification():
    valid_token = settings.valid_tokens[0]
    user = TokenVerifier.verify(valid_token)
    assert user is not None
    assert user.token == valid_token


def test_bearer_prefix_token_verification():
    valid_token = settings.valid_tokens[0]
    user = TokenVerifier.verify(f"Bearer {valid_token}")
    assert user is not None
    assert user.token == valid_token


def test_invalid_token_verification():
    user = TokenVerifier.verify("invalid-token-12345")
    assert user is None


def test_empty_token_verification():
    user = TokenVerifier.verify("")
    assert user is None
