"""
ArchMCP - Persistent Cryptographic Key Store Repository.

Manages secure storage, hashed verification, lifecycle transitions,
and rotation of API keys without exposing plaintext secrets.

@author Shubham Upadhyay
@license MIT
"""

import json
import os
import threading
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone

from .models import ApiKeyRecord, TokenStatus
from .crypto import (
    generate_api_key,
    hash_token_secret,
    constant_time_verify,
    parse_token
)

logger = logging.getLogger(__name__)


class KeyStore:
    """
    Thread-safe persistent key store for hashed API keys.
    """

    def __init__(self, file_path: Optional[str] = "data/keystore.json") -> None:
        self.file_path = file_path
        self._lock = threading.RLock()
        self._keys: Dict[str, ApiKeyRecord] = {}
        if self.file_path and os.path.exists(self.file_path):
            self.load()

    def load(self) -> None:
        """
        Loads key records from persistent JSON file storage.

        @return None
        """
        with self._lock:
            try:
                if not self.file_path or not os.path.exists(self.file_path):
                    return
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for kid, record_dict in data.items():
                        self._keys[kid] = ApiKeyRecord.model_validate(record_dict)
                logger.info(f"Loaded {len(self._keys)} API keys from {self.file_path}")
            except Exception as e:
                logger.error(f"Failed to load keystore from {self.file_path}: {e}")

    def save(self) -> None:
        """
        Flushes in-memory key records to persistent storage atomically.

        @return None
        """
        with self._lock:
            if not self.file_path:
                return
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self.file_path)), exist_ok=True)
                data = {kid: record.model_dump(mode="json") for kid, record in self._keys.items()}
                temp_file = f"{self.file_path}.tmp"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
                if os.path.exists(self.file_path):
                    os.replace(temp_file, self.file_path)
                else:
                    os.rename(temp_file, self.file_path)
            except Exception as e:
                logger.error(f"Failed to persist keystore to {self.file_path}: {e}")

    def create_key(
        self,
        name: str,
        scopes: Optional[List[str]] = None,
        owner: str = "system",
        tenant_id: str = "default",
        environment: str = "live",
        expires_in_days: Optional[int] = None
    ) -> Tuple[ApiKeyRecord, str]:
        """
        Generates a new cryptographic API key, stores its hash, and returns
        the record along with the one-time raw plaintext token.

        @param str name: Descriptive name
        @param Optional[List[str]] scopes: List of granted permission scopes
        @param str owner: Owning user or service
        @param str tenant_id: Tenant organization
        @param str environment: 'live', 'test', 'dev'
        @param Optional[int] expires_in_days: Days until expiration, or None for no expiration
        @return Tuple[ApiKeyRecord, str]: (ApiKeyRecord, raw_plaintext_token)
        """
        raw_token, kid, secret = generate_api_key(environment=environment)
        secret_hash, salt = hash_token_secret(secret=secret)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=expires_in_days) if expires_in_days else None

        record = ApiKeyRecord(
            kid=kid,
            name=name,
            secret_hash=secret_hash,
            salt=salt,
            environment=environment,
            scopes=scopes or ["*"],
            owner=owner,
            tenant_id=tenant_id,
            status=TokenStatus.ACTIVE,
            created_at=now,
            expires_at=expires_at,
            last_used_at=None
        )

        with self._lock:
            self._keys[kid] = record
            self.save()

        logger.info(f"Created new API key '{name}' (kid: {kid}, tenant: {tenant_id})")
        return record, raw_token

    def verify_token(self, raw_token: str) -> Optional[ApiKeyRecord]:
        """
        Verifies an incoming raw token string against stored hashes.
        Uses constant-time comparison to eliminate timing attacks.

        @param str raw_token: Incoming raw bearer token
        @return Optional[ApiKeyRecord]: Valid key record or None if invalid/expired/revoked
        """
        parsed = parse_token(raw_token)
        if not parsed:
            return None

        _, _, kid, secret = parsed

        with self._lock:
            record = self._keys.get(kid)
            if not record:
                return None

            # Check if expired
            if record.expires_at and datetime.now(timezone.utc) > record.expires_at:
                if record.status != TokenStatus.EXPIRED:
                    record.status = TokenStatus.EXPIRED
                    self.save()
                return None

            if record.status != TokenStatus.ACTIVE:
                return None

            # Constant-time comparison
            if not constant_time_verify(secret=secret, salt=record.salt, expected_hash=record.secret_hash):
                return None

            # Update last used timestamp
            record.last_used_at = datetime.now(timezone.utc)
            self.save()
            return record

    def revoke_key(self, kid: str) -> bool:
        """
        Immediately revokes an active API key.

        @param str kid: Key ID to revoke
        @return bool: True if revoked, False if not found
        """
        with self._lock:
            record = self._keys.get(kid)
            if not record:
                return False
            record.status = TokenStatus.REVOKED
            self.save()
            logger.info(f"Revoked API key kid: {kid}")
            return True

    def rotate_key(
        self,
        kid: str,
        expires_in_days: Optional[int] = None
    ) -> Optional[Tuple[ApiKeyRecord, str]]:
        """
        Rotates an existing key: revokes the old key and generates a new key with identical properties.

        @param str kid: Key ID to rotate
        @param Optional[int] expires_in_days: New expiration duration
        @return Optional[Tuple[ApiKeyRecord, str]]: (New KeyRecord, new raw plaintext token) or None
        """
        with self._lock:
            old_record = self._keys.get(kid)
            if not old_record:
                return None

            # Revoke old key
            old_record.status = TokenStatus.REVOKED

            # Create replacement key
            new_record, new_token = self.create_key(
                name=f"{old_record.name} (Rotated)",
                scopes=old_record.scopes,
                owner=old_record.owner,
                tenant_id=old_record.tenant_id,
                environment=old_record.environment,
                expires_in_days=expires_in_days
            )
            self.save()
            logger.info(f"Rotated key {kid} -> new key {new_record.kid}")
            return new_record, new_token

    def get_key(self, kid: str) -> Optional[ApiKeyRecord]:
        """
        Retrieves a key record by Key ID.

        @param str kid: Key identifier
        @return Optional[ApiKeyRecord]: Record or None
        """
        with self._lock:
            return self._keys.get(kid)

    def list_keys(
        self,
        tenant_id: Optional[str] = None,
        include_revoked: bool = False
    ) -> List[ApiKeyRecord]:
        """
        Returns key records matching tenant and filter criteria.

        @param Optional[str] tenant_id: Tenant filter
        @param bool include_revoked: If True, includes revoked/expired keys
        @return List[ApiKeyRecord]: Matching key records
        """
        with self._lock:
            results = []
            for record in self._keys.values():
                if tenant_id and record.tenant_id != tenant_id:
                    continue
                if not include_revoked and record.status != TokenStatus.ACTIVE:
                    continue
                results.append(record)
            return sorted(results, key=lambda k: k.created_at, reverse=True)

    def clear(self) -> None:
        """
        Clears all stored keys in memory and removes disk file if applicable (used for tests).

        @return None
        """
        with self._lock:
            self._keys.clear()
            if self.file_path and os.path.exists(self.file_path):
                try:
                    os.remove(self.file_path)
                except Exception:
                    pass


# Global singleton keystore instance
keystore = KeyStore()
