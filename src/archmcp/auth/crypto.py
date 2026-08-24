"""
ArchMCP - Cryptographic Token & Hashing Engine.

Provides cryptographically secure random token generation, salted HMAC-SHA256 hashing,
constant-time string comparisons, and structured token parsing.

@author Shubham Upadhyay
@license MIT
"""

import hmac
import hashlib
import secrets
from typing import Optional, Tuple


# Key format: arch_{environment}_{kid}_{secret}
# Example: arch_live_k9a2f1b4_x8F3kLm9Q2w...
TOKEN_PREFIX = "arch"


def generate_token_secret(length_bytes: int = 32) -> str:
    """
    Generates a cryptographically secure URL-safe random string for token secret.

    @param int length_bytes: Number of random bytes of entropy (default 32)
    @return str: URL-safe base64-encoded secret
    """
    return secrets.token_urlsafe(length_bytes)


def generate_key_id(length_bytes: int = 6) -> str:
    """
    Generates a unique key identifier (kid).

    @param int length_bytes: Number of random bytes
    @return str: Hex string key identifier
    """
    return secrets.token_hex(length_bytes)


def generate_api_key(
    environment: str = "live",
    prefix: str = TOKEN_PREFIX,
    secret_bytes: int = 32
) -> Tuple[str, str, str]:
    """
    Generates a structured API key token with unique key ID and high-entropy secret.

    Format: {prefix}_{environment}_{kid}_{secret}

    @param str environment: Environment identifier ('live', 'test', 'dev')
    @param str prefix: Brand prefix (default 'arch')
    @param int secret_bytes: Entropy byte length
    @return Tuple[str, str, str]: (raw_full_token, key_id, raw_secret)
    """
    kid = generate_key_id()
    secret = generate_token_secret(length_bytes=secret_bytes)
    raw_token = f"{prefix}_{environment}_{kid}_{secret}"
    return raw_token, kid, secret


def hash_token_secret(secret: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Computes a cryptographic salted HMAC-SHA256 hash of a token secret.

    @param str secret: Raw plaintext secret
    @param Optional[str] salt: Optional existing salt, or new random salt generated if None
    @return Tuple[str, str]: (hex_digest_hash, salt_hex)
    """
    if not salt:
        salt = secrets.token_hex(16)

    hash_digest = hmac.new(
        key=salt.encode("utf-8"),
        msg=secret.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()

    return hash_digest, salt


def constant_time_verify(secret: str, salt: str, expected_hash: str) -> bool:
    """
    Verifies a plaintext secret against a salted hash using constant-time comparison
    to prevent timing side-channel attacks.

    @param str secret: Provided plaintext secret
    @param str salt: Stored salt for the key
    @param str expected_hash: Stored cryptographic hash
    @return bool: True if secret matches expected hash, False otherwise
    """
    computed_hash, _ = hash_token_secret(secret=secret, salt=salt)
    return hmac.compare_digest(computed_hash, expected_hash)


def parse_token(raw_token: str) -> Optional[Tuple[str, str, str, str]]:
    """
    Parses a formatted API key token into its constituent components.

    Expected format: {prefix}_{environment}_{kid}_{secret}

    @param str raw_token: Raw token string from Authorization header or parameter
    @return Optional[Tuple[str, str, str, str]]: (prefix, environment, kid, secret) or None if invalid format
    """
    if not raw_token:
        return None

    clean = raw_token.strip()
    if clean.lower().startswith("bearer "):
        clean = clean[7:].strip()

    parts = clean.split("_")
    # Must have prefix, environment, kid, and secret
    if len(parts) < 4:
        return None

    prefix = parts[0]
    environment = parts[1]
    kid = parts[2]
    secret = "_".join(parts[3:])

    if not prefix or not environment or not kid or not secret:
        return None

    return prefix, environment, kid, secret
