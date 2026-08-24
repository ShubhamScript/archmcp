"""Tests for fine-grained RBAC scopes and MCP tool permission enforcement."""

import json
from archmcp.auth.permissions import Scope, has_required_scopes, ROLE_PROFILES
from archmcp.mcp.tools import validate_scope
from archmcp.storage.database import db
from archmcp.models.service import ServiceMetadata, DatabaseTable, APIEndpoint


def setup_module():
    db.clear()
    db.save_service(ServiceMetadata(
        id="auth-service",
        name="Auth Service",
        apis=[APIEndpoint(path="/login", method="POST", summary="Login")],
        database_tables=[DatabaseTable(name="users", columns=["id", "username", "password_hash"])]
    ))


def test_has_required_scopes_wildcard():
    # Wildcard user has all permissions
    assert has_required_scopes(["*"], Scope.ARCH_READ.value) is True
    assert has_required_scopes(["*"], Scope.ARCH_SCHEMA_READ.value) is True
    assert has_required_scopes(["*"], [Scope.ARCH_BLAST_RADIUS.value, Scope.ARCH_WRITE.value]) is True


def test_has_required_scopes_granular():
    viewer_scopes = ["arch:read"]
    assert has_required_scopes(viewer_scopes, "arch:read") is True
    assert has_required_scopes(viewer_scopes, "arch:schema:read") is False
    assert has_required_scopes(viewer_scopes, "arch:blast_radius") is False

    schema_reader_scopes = ["arch:read", "arch:schema:read"]
    assert has_required_scopes(schema_reader_scopes, "arch:schema:read") is True
    assert has_required_scopes(schema_reader_scopes, "arch:blast_radius") is False


def test_role_profiles():
    assert Scope.ALL.value in ROLE_PROFILES["admin"]
    assert Scope.ARCH_SCHEMA_READ.value in ROLE_PROFILES["architect"]
    assert Scope.ARCH_SCHEMA_READ.value not in ROLE_PROFILES["viewer"]


def test_validate_scope_helper():
    # Allowed
    assert validate_scope("search_microservices", Scope.ARCH_READ.value, ["arch:read"]) is None
    assert validate_scope("get_database_schema", Scope.ARCH_SCHEMA_READ.value, ["*"]) is None

    # Forbidden
    res_denied = validate_scope("get_database_schema", Scope.ARCH_SCHEMA_READ.value, ["arch:read"])
    assert res_denied is not None
    data = json.loads(res_denied)
    assert "Forbidden" in data["error"]
    assert data["required_scope"] == "arch:schema:read"
