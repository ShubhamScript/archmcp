"""
ArchMCP - Enterprise Token Verifier & Authentication Dispatcher.

Coordinates token validation across persistent cryptographic KeyStore (API Keys)
and enterprise OIDC / OAuth2 JWT providers with constant-time validation and audit logging.

@author Shubham Upadhyay
@license MIT
"""

from typing import Optional
from ..config.settings import settings
from .models import AuthUser
from .key_store import keystore
from .oidc import oidc_provider
from .audit import audit_logger, AuditEventType
from .permissions import Scope


class TokenVerifier:
    """
    Validates incoming bearer tokens and queries against KeyStore and OIDC providers.
    """

    @staticmethod
    def verify(
        token: Optional[str],
        client_ip: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Optional[AuthUser]:
        """
        Validates a bearer or query token against configured authentication providers.

        @param Optional[str] token: Raw token string from request header or query
        @param Optional[str] client_ip: Originating client IP
        @param Optional[str] request_id: Correlation identifier
        @return Optional[AuthUser]: Validated user entity or None if unauthorized
        """
        if not settings.AUTH_ENABLED:
            return AuthUser(
                token_id="anon-000",
                username="guest",
                scopes=[Scope.ALL.value],
                tenant_id="default",
                is_authenticated=False,
                token_name="Anonymous Access"
            )

        if not token:
            audit_logger.log(
                event_type=AuditEventType.AUTH_FAILURE,
                action="auth:missing_token",
                actor="anonymous",
                client_ip=client_ip,
                status="DENIED",
                details={"reason": "Missing token header or parameter"},
                request_id=request_id
            )
            return None

        # Clean token format (strip "Bearer " if sent in HTTP Authorization header)
        clean_token = token.strip()
        if clean_token.lower().startswith("bearer "):
            clean_token = clean_token[7:].strip()

        if not clean_token:
            return None

        # 1. API Key Provider (keys starting with 'arch_')
        if clean_token.startswith("arch_"):
            record = keystore.verify_token(clean_token)
            if record:
                user = AuthUser(
                    token_id=record.kid,
                    username=record.owner,
                    scopes=record.scopes,
                    tenant_id=record.tenant_id,
                    is_authenticated=True,
                    token_name=record.name
                )
                audit_logger.log(
                    event_type=AuditEventType.AUTH_SUCCESS,
                    action="auth:api_key",
                    actor=user.username,
                    tenant_id=user.tenant_id,
                    client_ip=client_ip,
                    status="SUCCESS",
                    details={"kid": record.kid, "key_name": record.name},
                    request_id=request_id
                )
                return user
            else:
                audit_logger.log(
                    event_type=AuditEventType.AUTH_FAILURE,
                    action="auth:api_key",
                    actor="invalid-key",
                    client_ip=client_ip,
                    status="DENIED",
                    details={"reason": "Invalid, expired, or revoked API key"},
                    request_id=request_id
                )
                return None

        # 2. OIDC / OAuth2 JWT Provider (tokens starting with 'eyJ')
        if clean_token.startswith("eyJ"):
            user = oidc_provider.verify_token(clean_token)
            if user:
                audit_logger.log(
                    event_type=AuditEventType.AUTH_SUCCESS,
                    action="auth:oidc_jwt",
                    actor=user.username,
                    tenant_id=user.tenant_id,
                    client_ip=client_ip,
                    status="SUCCESS",
                    details={"token_id": user.token_id, "scopes": user.scopes},
                    request_id=request_id
                )
                return user
            else:
                audit_logger.log(
                    event_type=AuditEventType.AUTH_FAILURE,
                    action="auth:oidc_jwt",
                    actor="invalid-jwt",
                    client_ip=client_ip,
                    status="DENIED",
                    details={"reason": "Invalid or expired OIDC JWT token"},
                    request_id=request_id
                )
                return None

        # 3. Deny unrecognized format
        audit_logger.log(
            event_type=AuditEventType.AUTH_FAILURE,
            action="auth:unknown_format",
            actor="unrecognized",
            client_ip=client_ip,
            status="DENIED",
            details={"reason": "Unrecognized token format. Expected 'arch_*' API key or 'eyJ*' OIDC JWT."},
            request_id=request_id
        )
        return None
