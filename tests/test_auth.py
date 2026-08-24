"""Tests for authentication and token verification in ArchMCP."""

from archmcp.auth.token_verifier import TokenVerifier
from archmcp.auth.key_store import keystore


def test_valid_api_key_verification():
    record, raw_token = keystore.create_key(
        name="Auth Test Key",
        scopes=["arch:read", "arch:blast_radius"],
        owner="security-team",
        tenant_id="tenant-test"
    )

    user = TokenVerifier.verify(raw_token)
    assert user is not None
    assert user.token_id == record.kid
    assert user.username == "security-team"
    assert user.tenant_id == "tenant-test"
    assert "arch:read" in user.scopes


def test_bearer_prefix_api_key_verification():
    record, raw_token = keystore.create_key(name="Bearer Test Key")
    user = TokenVerifier.verify(f"Bearer {raw_token}")
    assert user is not None
    assert user.token_id == record.kid


def test_invalid_token_verification():
    user = TokenVerifier.verify("invalid-token-12345")
    assert user is None


def test_empty_token_verification():
    user = TokenVerifier.verify("")
    assert user is None
    user_none = TokenVerifier.verify(None)
    assert user_none is None
