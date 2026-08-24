"""Integration tests for CLI key management, rate limit headers, correlation IDs, and probes."""

from starlette.testclient import TestClient
from archmcp.main import app
from archmcp.auth.key_store import keystore
from archmcp.auth.rate_limiter import limiter
from archmcp.cli import (
    cmd_keys_create,
    cmd_keys_list,
    cmd_keys_revoke,
    cmd_keys_rotate
)
import argparse


def test_health_live_and_ready():
    client = TestClient(app, base_url="http://localhost:8000")
    res_live = client.get("/health/live")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "alive"

    res_ready = client.get("/health/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"


def test_correlation_id_propagation():
    client = TestClient(app, base_url="http://localhost:8000")
    # Send custom X-Request-ID
    res = client.get("/health", headers={"X-Request-ID": "custom-trace-uuid-12345"})
    assert res.status_code == 200
    assert res.headers["X-Request-ID"] == "custom-trace-uuid-12345"


def test_authenticated_request_with_rate_limit_headers():
    client = TestClient(app, base_url="http://localhost:8000")
    limiter.reset()

    record, raw_token = keystore.create_key(name="Client Integration Key")

    # Send authorized request with Bearer header
    res = client.get("/api/dashboard/data", headers={"Authorization": f"Bearer {raw_token}"})
    assert res.status_code == 200
    assert "X-RateLimit-Limit" in res.headers
    assert "X-RateLimit-Remaining" in res.headers


def test_cli_keys_commands(capsys):
    # Test CLI keys create
    args_create = argparse.Namespace(
        name="CLI Test Key",
        role="architect",
        scopes=None,
        owner="cli-user",
        tenant="cli-tenant",
        env="live",
        expires=30
    )
    cmd_keys_create(args_create)
    captured = capsys.readouterr().out
    assert "NEW API KEY CREATED" in captured
    assert "arch_live_" in captured

    # Test CLI keys list
    args_list = argparse.Namespace(tenant=None, all=True)
    cmd_keys_list(args_list)
    captured_list = capsys.readouterr().out
    assert "CLI Test Key" in captured_list

    # Extract created kid
    keys = keystore.list_keys(tenant_id="cli-tenant")
    assert len(keys) > 0
    kid = keys[0].kid

    # Test CLI keys rotate
    args_rotate = argparse.Namespace(kid=kid, expires=15)
    cmd_keys_rotate(args_rotate)
    captured_rotate = capsys.readouterr().out
    assert "API KEY ROTATED" in captured_rotate

    # Test CLI keys revoke
    args_revoke = argparse.Namespace(kid=kid)
    cmd_keys_revoke(args_revoke)
    captured_revoke = capsys.readouterr().out
    assert "Successfully revoked" in captured_revoke
