"""Tests for structured security audit logging."""

from archmcp.auth.audit import SecurityAuditLogger, AuditEventType


def test_audit_logger_event_emission():
    logger = SecurityAuditLogger(log_file=None, buffer_size=10)
    logger.clear()

    # Log an auth success event
    event = logger.log(
        event_type=AuditEventType.AUTH_SUCCESS,
        action="auth:login",
        actor="engineer-1",
        tenant_id="acme-corp",
        client_ip="192.168.1.100",
        status="SUCCESS",
        details={"method": "api_key"}
    )

    assert event.event_id is not None
    assert event.event_type == AuditEventType.AUTH_SUCCESS
    assert event.actor == "engineer-1"
    assert event.tenant_id == "acme-corp"

    # Fetch recent events
    recent = logger.get_recent_events(limit=5)
    assert len(recent) == 1
    assert recent[0].action == "auth:login"


def test_audit_logger_filtering():
    logger = SecurityAuditLogger(log_file=None, buffer_size=10)
    logger.clear()

    logger.log(event_type=AuditEventType.AUTH_SUCCESS, action="act1", tenant_id="tenant-1")
    logger.log(event_type=AuditEventType.AUTH_FAILURE, action="act2", tenant_id="tenant-2")
    logger.log(event_type=AuditEventType.TOOL_INVOCATION, action="act3", tenant_id="tenant-1")

    # Filter by event type
    failures = logger.get_recent_events(event_type=AuditEventType.AUTH_FAILURE)
    assert len(failures) == 1
    assert failures[0].action == "act2"

    # Filter by tenant
    tenant1 = logger.get_recent_events(tenant_id="tenant-1")
    assert len(tenant1) == 2
