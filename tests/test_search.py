"""Tests for search and knowledge services in ArchMCP."""

from archmcp.repositories.repository_registry import RepositoryRegistry
from archmcp.ingestion.repository_scanner import RepositoryScanner
from archmcp.services.search_service import SearchService
from archmcp.services.knowledge_service import KnowledgeService
from archmcp.services.architecture_service import ArchitectureService


def setup_module():
    """Ensure data is loaded before running tests."""
    registry = RepositoryRegistry("data/repositories.yaml")
    scanner = RepositoryScanner(registry)
    scanner.scan_and_index_all()


def test_search_services():
    search = SearchService()
    results = search.search_microservices("payment")
    assert len(results) > 0
    matched_ids = [r["id"] for r in results]
    assert "payment-service" in matched_ids


def test_find_api_by_route():
    knowledge = KnowledgeService()
    results = knowledge.find_api_by_route("/api/v1/orders")
    assert len(results) > 0
    assert any(r["service_id"] == "order-service" for r in results)


def test_find_table_owner():
    knowledge = KnowledgeService()
    results = knowledge.find_table_owner("transactions")
    assert len(results) > 0
    assert results[0]["service_id"] == "payment-service"


def test_architecture_dependencies():
    arch = ArchitectureService()
    deps = arch.get_service_dependencies("order-service")
    assert deps is not None
    assert "payment-service" in deps["declared_downstream"]
    assert "auth-service" in deps["declared_upstream"]
