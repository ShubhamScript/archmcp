"""
ArchMCP - Authentication & Identity Data Models.

@author Shubham Upadhyay
@license MIT
"""

from enum import Enum
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class TokenStatus(str, Enum):
    """Lifecycle status of an API authentication key."""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ApiKeyRecord(BaseModel):
    """
    Persistent record representing an API key stored securely in the KeyStore.
    Plaintext secrets are never stored; only the salted HMAC-SHA256 hash is retained.
    """
    kid: str = Field(description="Unique key identifier, public prefix")
    name: str = Field(description="Human readable name or purpose of the key (e.g. 'Claude Desktop', 'CI Pipeline')")
    secret_hash: str = Field(description="Cryptographic salted HMAC-SHA256 hash of the token secret")
    salt: str = Field(description="Unique per-key cryptographic salt")
    environment: str = Field(default="live", description="Environment tier: 'live', 'test', 'dev'")
    scopes: List[str] = Field(default_factory=lambda: ["*"], description="Granular permissions granted to this key")
    owner: str = Field(default="system", description="Owner username or team name")
    tenant_id: str = Field(default="default", description="Multi-tenant boundary identifier")
    status: TokenStatus = Field(default=TokenStatus.ACTIVE, description="Current lifecycle status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Optional expiration timestamp")
    last_used_at: Optional[datetime] = Field(default=None, description="Timestamp of most recent authorized usage")

    def is_valid(self) -> bool:
        """
        Checks if key is currently active and has not expired.

        @return bool: True if key is active and non-expired
        """
        if self.status != TokenStatus.ACTIVE:
            return False
        if self.expires_at is not None:
            now = datetime.now(timezone.utc)
            if now > self.expires_at:
                return False
        return True


class AuthUser(BaseModel):
    """
    Authenticated caller principal context attached to request state and audit logs.
    """
    token_id: str = Field(description="Key ID or Subject Identifier")
    username: str = Field(description="Human or service identifier")
    scopes: List[str] = Field(default_factory=list, description="Granted permission scopes")
    tenant_id: str = Field(default="default", description="Tenant organization ID")
    is_authenticated: bool = Field(default=True, description="Authentication flag")
    token_name: Optional[str] = Field(default=None, description="Friendly name of the key")
