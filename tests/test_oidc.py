"""Tests for OIDC / OAuth2 JWT bearer token verification."""

import json
import base64
import time
from archmcp.auth.oidc import OIDCAuthProvider


def make_jwt(payload: dict) -> str:
    header = {"alg": "RS256", "typ": "JWT"}
    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = base64.urlsafe_b64encode(b"mock_signature_bytes").decode().rstrip("=")
    return f"{h_b64}.{p_b64}.{sig}"


def test_oidc_valid_jwt():
    provider = OIDCAuthProvider()
    payload = {
        "sub": "user_12345",
        "email": "alice@company.com",
        "scope": "arch:read arch:schema:read",
        "tenant_id": "corp-eng",
        "exp": time.time() + 3600
    }
    token = make_jwt(payload)
    user = provider.verify_token(token)

    assert user is not None
    assert user.username == "alice@company.com"
    assert user.tenant_id == "corp-eng"
    assert "arch:read" in user.scopes
    assert "arch:schema:read" in user.scopes


def test_oidc_expired_jwt():
    provider = OIDCAuthProvider()
    payload = {
        "sub": "user_expired",
        "exp": time.time() - 3600  # Expired 1 hour ago
    }
    token = make_jwt(payload)
    user = provider.verify_token(token)
    assert user is None


def test_oidc_role_mapping():
    provider = OIDCAuthProvider()
    payload = {
        "sub": "admin_user",
        "roles": ["admin"],
        "exp": time.time() + 3600
    }
    token = make_jwt(payload)
    user = provider.verify_token(token)

    assert user is not None
    assert "*" in user.scopes
