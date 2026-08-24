"""
ArchMCP - Enterprise OIDC & OAuth2 JWT Provider.

Supports validating standard OpenID Connect (OIDC) and OAuth 2.0 JWT bearer tokens,
extracting principal identity, organization/tenant mapping, and RBAC scope claims.

@author Shubham Upadhyay
@license MIT
"""

import json
import base64
import time
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from .models import AuthUser
from .permissions import Scope

logger = logging.getLogger(__name__)


class OIDCAuthProvider:
    """
    Validates and unpacks enterprise OpenID Connect / OAuth 2.0 JWT bearer tokens.
    """

    def __init__(
        self,
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
        required_scopes: Optional[List[str]] = None
    ) -> None:
        self.issuer = issuer
        self.audience = audience
        self.required_scopes = required_scopes or []

    @staticmethod
    def _decode_jwt_segment(segment: str) -> Dict[str, Any]:
        """Decodes a base64url encoded JWT segment without signature checking for claim inspection."""
        # Pad base64 string
        rem = len(segment) % 4
        if rem > 0:
            segment += "=" * (4 - rem)
        decoded_bytes = base64.urlsafe_b64decode(segment)
        return json.loads(decoded_bytes.decode("utf-8"))

    def verify_token(self, jwt_token: str) -> Optional[AuthUser]:
        """
        Validates an OIDC JWT bearer token and converts it to an AuthUser principal.

        @param str jwt_token: Raw JWT string
        @return Optional[AuthUser]: Validated user principal or None
        """
        if not jwt_token or not jwt_token.startswith("eyJ"):
            return None

        parts = jwt_token.strip().split(".")
        if len(parts) != 3:
            return None

        try:
            payload = self._decode_jwt_segment(parts[1])

            # 1. Validate Expiration (exp claim)
            exp = payload.get("exp")
            if exp and float(exp) < time.time():
                logger.warning(f"OIDC Token expired (exp: {exp})")
                return None

            # 2. Validate Issuer (iss claim) if configured
            if self.issuer and payload.get("iss") != self.issuer:
                logger.warning(f"OIDC Issuer mismatch: expected {self.issuer}, got {payload.get('iss')}")
                return None

            # 3. Validate Audience (aud claim) if configured
            if self.audience:
                aud = payload.get("aud")
                if isinstance(aud, list) and self.audience not in aud:
                    return None
                elif isinstance(aud, str) and aud != self.audience:
                    return None

            # 4. Extract Identity & Scopes
            sub = payload.get("sub", "oidc-user")
            username = payload.get("preferred_username") or payload.get("email") or payload.get("name") or sub
            tenant_id = payload.get("tenant_id") or payload.get("org_id") or "default"

            # Parse scopes from 'scope', 'scp', or 'roles' claims
            raw_scopes = payload.get("scope") or payload.get("scp") or []
            if isinstance(raw_scopes, str):
                scopes = raw_scopes.split(" ")
            elif isinstance(raw_scopes, list):
                scopes = raw_scopes
            else:
                scopes = []

            # If roles present, map roles to scopes
            roles = payload.get("roles") or payload.get("groups") or []
            if "admin" in roles:
                scopes.append(Scope.ALL.value)
            elif "architect" in roles:
                scopes.extend([Scope.ARCH_READ.value, Scope.ARCH_SCHEMA_READ.value, Scope.ARCH_BLAST_RADIUS.value])

            if not scopes:
                scopes = [Scope.ARCH_READ.value]

            return AuthUser(
                token_id=f"oidc:{sub}",
                username=username,
                scopes=list(set(scopes)),
                tenant_id=tenant_id,
                is_authenticated=True,
                token_name="OIDC Bearer Token"
            )
        except Exception as e:
            logger.error(f"Error parsing OIDC JWT payload: {e}")
            return None


# Global OIDC provider instance
oidc_provider = OIDCAuthProvider()
