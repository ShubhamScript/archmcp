"""Tests for repository registry and scanner in ArchMCP."""

from archmcp.repositories.repository_registry import RepositoryRegistry
from archmcp.ingestion.repository_scanner import RepositoryScanner
from archmcp.storage.database import db


def test_repository_registry_loading():
    registry = RepositoryRegistry("data/repositories.yaml")
    registry.load()
    services = registry.get_all_services()
    assert len(services) > 0
    service_ids = [s.id for s in services]
    assert "auth-service" in service_ids
    assert "order-service" in service_ids
    assert "payment-service" in service_ids


def test_repository_scanner():
    registry = RepositoryRegistry("data/repositories.yaml")
    scanner = RepositoryScanner(registry)
    count = scanner.scan_and_index_all()
    assert count > 0

    auth_svc = db.get_service("auth-service")
    assert auth_svc is not None
    assert auth_svc.name == "Authentication & Identity Service"
    assert len(auth_svc.apis) > 0
    assert len(auth_svc.database_tables) > 0
