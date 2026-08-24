"""Tests for multi-tenant data boundary isolation."""

from archmcp.storage.database import db
from archmcp.models.service import ServiceMetadata
from archmcp.models.document import Document


def test_database_multi_tenant_isolation():
    db.clear()

    # Service for Tenant Alpha
    db.save_service(ServiceMetadata(
        id="alpha-service",
        name="Alpha Service",
        tenant_id="tenant-alpha"
    ))

    # Service for Tenant Beta
    db.save_service(ServiceMetadata(
        id="beta-service",
        name="Beta Service",
        tenant_id="tenant-beta"
    ))

    # Documents for tenants
    db.save_document(Document(id="doc-alpha", title="Alpha Architecture", content="Secret Alpha", tenant_id="tenant-alpha"))
    db.save_document(Document(id="doc-beta", title="Beta Architecture", content="Secret Beta", tenant_id="tenant-beta"))

    # Verify listing by tenant
    alpha_services = db.list_services(tenant_id="tenant-alpha")
    assert len(alpha_services) == 1
    assert alpha_services[0].id == "alpha-service"

    beta_services = db.list_services(tenant_id="tenant-beta")
    assert len(beta_services) == 1
    assert beta_services[0].id == "beta-service"

    # Cross-tenant direct lookup should be blocked
    assert db.get_service("alpha-service", tenant_id="tenant-beta") is None
    assert db.get_service("alpha-service", tenant_id="tenant-alpha") is not None

    # Document isolation
    assert db.get_document("doc-alpha", tenant_id="tenant-beta") is None
    assert db.get_document("doc-alpha", tenant_id="tenant-alpha") is not None
