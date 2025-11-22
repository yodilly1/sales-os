"""Security utilities and helpers."""

import hashlib
import secrets
from typing import Optional


def generate_api_key(prefix: str = "sk_", length: int = 32) -> str:
    """
    Generate a secure API key.

    Args:
        prefix: Key prefix for identification
        length: Length of the random portion

    Returns:
        Generated API key string
    """
    random_bytes = secrets.token_urlsafe(length)
    return f"{prefix}{random_bytes}"


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for secure storage.

    Args:
        api_key: Raw API key

    Returns:
        SHA-256 hash of the API key
    """
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """
    Verify an API key against its stored hash.

    Args:
        raw_key: The raw API key to verify
        stored_hash: The stored hash to compare against

    Returns:
        True if key matches, False otherwise
    """
    return secrets.compare_digest(hash_api_key(raw_key), stored_hash)


def generate_state_token(length: int = 32) -> str:
    """
    Generate a secure state token for OAuth flows.

    Args:
        length: Length of the token

    Returns:
        Random state token
    """
    return secrets.token_urlsafe(length)


def generate_verification_token(length: int = 32) -> str:
    """
    Generate a secure verification token for email verification, etc.

    Args:
        length: Length of the token

    Returns:
        Random verification token
    """
    return secrets.token_urlsafe(length)


def mask_email(email: str) -> str:
    """
    Mask an email address for logging/display.

    Args:
        email: Full email address

    Returns:
        Masked email (e.g., "j***@example.com")
    """
    if "@" not in email:
        return "***"

    local, domain = email.split("@", 1)
    if len(local) <= 1:
        masked_local = "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 1)

    return f"{masked_local}@{domain}"


def mask_api_key(api_key: str, visible_chars: int = 8) -> str:
    """
    Mask an API key for logging/display.

    Args:
        api_key: Full API key
        visible_chars: Number of characters to show

    Returns:
        Masked API key (e.g., "sk_abc123...xyz")
    """
    if len(api_key) <= visible_chars:
        return api_key

    return api_key[:visible_chars] + "..." + api_key[-4:]


def get_client_ip(
    x_forwarded_for: Optional[str] = None,
    x_real_ip: Optional[str] = None,
    remote_addr: Optional[str] = None,
) -> Optional[str]:
    """
    Extract client IP from headers, handling proxies.

    Args:
        x_forwarded_for: X-Forwarded-For header value
        x_real_ip: X-Real-IP header value
        remote_addr: Direct remote address

    Returns:
        Client IP address or None
    """
    if x_forwarded_for:
        # Take the first IP in the chain (original client)
        return x_forwarded_for.split(",")[0].strip()

    if x_real_ip:
        return x_real_ip.strip()

    return remote_addr
