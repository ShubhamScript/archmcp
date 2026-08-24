"""
ArchMCP - Structured Security Audit Logger.

Provides immutable, structured JSON audit logging for security-relevant operations,
including authentication attempts, authorization decisions, token lifecycle events,
and MCP tool executions.

@author Shubham Upadhyay
@license MIT
"""

import json
import os
import uuid
import logging
import threading
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

logger = logging.getLogger("archmcp.security.audit")


class AuditEventType(str, Enum):
    """Types of auditable security events."""
    AUTH_SUCCESS = "AUTH_SUCCESS"
    AUTH_FAILURE = "AUTH_FAILURE"
    TOKEN_CREATED = "TOKEN_CREATED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    TOKEN_ROTATED = "TOKEN_ROTATED"
    TOOL_INVOCATION = "TOOL_INVOCATION"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RATE_LIMITED = "RATE_LIMITED"


class SecurityAuditEvent(BaseModel):
    """Structured security audit event payload."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: AuditEventType
    actor: str = Field(default="anonymous", description="Principal username, key ID, or service")
    tenant_id: str = Field(default="default", description="Tenant organization boundary")
    client_ip: Optional[str] = Field(default=None, description="Originating client IP address")
    action: str = Field(description="Action attempted (e.g. 'tool:analyze_blast_radius', 'auth:verify')")
    status: str = Field(default="SUCCESS", description="'SUCCESS', 'FAILURE', 'DENIED'")
    details: Dict[str, Any] = Field(default_factory=dict, description="Contextual event metadata")
    request_id: Optional[str] = Field(default=None, description="Distributed correlation ID")


class SecurityAuditLogger:
    """
    Thread-safe structured audit logger with in-memory ring buffer and persistent JSON append log.
    """

    def __init__(self, log_file: Optional[str] = "data/audit.log", buffer_size: int = 500) -> None:
        self.log_file = log_file
        self.buffer_size = buffer_size
        self._buffer: List[SecurityAuditEvent] = []
        self._lock = threading.RLock()

    def log(
        self,
        event_type: AuditEventType,
        action: str,
        actor: str = "anonymous",
        tenant_id: str = "default",
        client_ip: Optional[str] = None,
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> SecurityAuditEvent:
        """
        Records a security audit event to buffer, file, and structured logger.

        @param AuditEventType event_type: Event classification
        @param str action: Action attempted or executed
        @param str actor: User or service principal
        @param str tenant_id: Tenant identifier
        @param Optional[str] client_ip: Client IP address
        @param str status: Execution status
        @param Optional[Dict[str, Any]] details: Contextual metadata
        @param Optional[str] request_id: Correlation ID
        @return SecurityAuditEvent: Recorded event record
        """
        event = SecurityAuditEvent(
            event_type=event_type,
            action=action,
            actor=actor,
            tenant_id=tenant_id,
            client_ip=client_ip,
            status=status,
            details=details or {},
            request_id=request_id
        )

        with self._lock:
            self._buffer.append(event)
            if len(self._buffer) > self.buffer_size:
                self._buffer.pop(0)

            # Persist to disk if path is specified
            if self.log_file:
                try:
                    os.makedirs(os.path.dirname(os.path.abspath(self.log_file)), exist_ok=True)
                    with open(self.log_file, "a", encoding="utf-8") as f:
                        f.write(event.model_dump_json() + "\n")
                except Exception as e:
                    logger.error(f"Failed writing security audit event to disk: {e}")

        logger.info(f"AUDIT [{event.event_type.value}] actor={event.actor} tenant={event.tenant_id} action={event.action} status={event.status}")
        return event

    def get_recent_events(
        self,
        limit: int = 50,
        event_type: Optional[AuditEventType] = None,
        tenant_id: Optional[str] = None
    ) -> List[SecurityAuditEvent]:
        """
        Retrieves recent audit events from buffer with optional filters.

        @param int limit: Max count to return
        @param Optional[AuditEventType] event_type: Event type filter
        @param Optional[str] tenant_id: Tenant filter
        @return List[SecurityAuditEvent]: Matching audit events
        """
        with self._lock:
            results = self._buffer[:]
            if event_type:
                results = [e for e in results if e.event_type == event_type]
            if tenant_id:
                results = [e for e in results if e.tenant_id == tenant_id]
            return list(reversed(results[-limit:]))

    def clear(self) -> None:
        """
        Clears the in-memory buffer (used for test isolation).

        @return None
        """
        with self._lock:
            self._buffer.clear()


# Global singleton audit logger
audit_logger = SecurityAuditLogger()
