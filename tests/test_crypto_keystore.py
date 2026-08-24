"""Tests for cryptographic token generation, hashing, and persistent KeyStore lifecycle."""

import time
from datetime import datetime, timedelta, timezone
from archmcp.auth.crypto import (
    generate_api_key,
    hash_token_secret,
    constant_time_verify,
    parse_token
)
from archmcp.auth.key_store import KeyStore
from archmcp.auth.models import TokenStatus


def test_api_key_generation_structure():
    raw_token, kid, secret = generate_api_key(environment="live")
    assert raw_token.startswith("arch_live_")
    assert kid in raw_token
    assert len(kid) == 12  # 6 bytes hex = 12 chars
    assert len(secret) > 20

    parsed = parse_token(raw_token)
    assert parsed is not None
    prefix, env, parsed_kid, parsed_secret = parsed
    assert prefix == "arch"
    assert env == "live"
    assert parsed_kid == kid
    assert parsed_secret == secret


def test_hash_token_and_constant_time_verification():
    secret = "sample_secure_secret_entropy_12345"
    hash_digest, salt = hash_token_secret(secret)
    assert len(hash_digest) == 64  # SHA256 hex string
    assert len(salt) == 32  # 16 bytes hex salt

    # Positive constant time verify
    assert constant_time_verify(secret, salt, hash_digest) is True

    # Negative constant time verify
    assert constant_time_verify("wrong_secret", salt, hash_digest) is False
    assert constant_time_verify(secret, "wrong_salt", hash_digest) is False


def test_keystore_create_and_verify(tmp_path):
    store_file = str(tmp_path / "test_keystore.json")
    store = KeyStore(file_path=store_file)

    record, raw_token = store.create_key(
        name="Test Service Key",
        scopes=["arch:read", "arch:schema:read"],
        owner="test-eng",
        tenant_id="tenant-a"
    )

    assert record.kid is not None
    assert record.status == TokenStatus.ACTIVE
    assert record.tenant_id == "tenant-a"

    # Verify with valid token
    verified = store.verify_token(raw_token)
    assert verified is not None
    assert verified.kid == record.kid
    assert verified.owner == "test-eng"
    assert verified.last_used_at is not None

    # Verify with corrupted token
    corrupted_token = raw_token[:-4] + "xxxx"
    assert store.verify_token(corrupted_token) is None

    # Verify with unknown kid
    assert store.verify_token("arch_live_unknownkid_invalidsecret12345") is None


def test_keystore_expiration(tmp_path):
    store_file = str(tmp_path / "test_keystore_exp.json")
    store = KeyStore(file_path=store_file)

    # Key that already expired in the past
    record, raw_token = store.create_key(
        name="Expired Key",
        scopes=["arch:read"],
        expires_in_days=-1
    )

    verified = store.verify_token(raw_token)
    assert verified is None
    assert store.get_key(record.kid).status == TokenStatus.EXPIRED


def test_keystore_revocation(tmp_path):
    store_file = str(tmp_path / "test_keystore_revoke.json")
    store = KeyStore(file_path=store_file)

    record, raw_token = store.create_key(name="Revocable Key")
    assert store.verify_token(raw_token) is not None

    # Revoke key
    assert store.revoke_key(record.kid) is True
    assert store.verify_token(raw_token) is None
    assert store.get_key(record.kid).status == TokenStatus.REVOKED


def test_keystore_rotation(tmp_path):
    store_file = str(tmp_path / "test_keystore_rotate.json")
    store = KeyStore(file_path=store_file)

    old_record, old_token = store.create_key(
        name="Legacy Key",
        scopes=["arch:read", "arch:blast_radius"],
        tenant_id="org-1"
    )

    # Rotate
    new_record, new_token = store.rotate_key(old_record.kid)
    assert new_record.kid != old_record.kid
    assert new_record.scopes == old_record.scopes
    assert new_record.tenant_id == "org-1"

    # Old token fails
    assert store.verify_token(old_token) is None
    # New token succeeds
    assert store.verify_token(new_token) is not None


def test_keystore_persistence_reload(tmp_path):
    store_file = str(tmp_path / "test_keystore_persist.json")
    store1 = KeyStore(file_path=store_file)
    record, raw_token = store1.create_key(name="Persistent Key")

    # Reload from disk in a fresh store instance
    store2 = KeyStore(file_path=store_file)
    verified = store2.verify_token(raw_token)
    assert verified is not None
    assert verified.kid == record.kid
