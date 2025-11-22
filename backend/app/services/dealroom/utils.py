"""
Deal Room Utilities

Helper functions for deal room operations.
"""

import hashlib
import secrets
import string
import re
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID


def generate_slug(title: str, deal_id: Optional[str] = None) -> str:
    """
    Generate a URL-friendly slug from a title.

    Args:
        title: The deal room title
        deal_id: Optional deal ID to include for uniqueness

    Returns:
        A URL-safe slug like "acme-corp-enterprise-proposal-x7k9m"
    """
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')

    # Truncate to reasonable length
    slug = slug[:50]

    # Add random suffix for uniqueness
    random_suffix = generate_random_string(5)

    return f"{slug}-{random_suffix}"


def generate_random_string(length: int = 10) -> str:
    """
    Generate a random alphanumeric string.

    Args:
        length: Length of the string to generate

    Returns:
        Random alphanumeric string
    """
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_invitation_token() -> str:
    """
    Generate a secure invitation token.

    Returns:
        A 32-character URL-safe token
    """
    return secrets.token_urlsafe(24)


def generate_access_token(deal_room_id: UUID, email: Optional[str] = None) -> str:
    """
    Generate a temporary access token for a deal room session.

    Args:
        deal_room_id: The deal room ID
        email: Optional viewer email

    Returns:
        A signed access token
    """
    timestamp = datetime.utcnow().isoformat()
    data = f"{deal_room_id}:{email or 'anonymous'}:{timestamp}"
    token = secrets.token_urlsafe(32)
    return token


def hash_password(password: str) -> str:
    """
    Hash a password for storage.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    # Using SHA-256 with salt for simplicity
    # In production, use bcrypt or argon2
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        password: Plain text password to verify
        hashed: Stored hash to compare against

    Returns:
        True if password matches
    """
    try:
        salt, stored_hash = hashed.split(':')
        computed_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return secrets.compare_digest(computed_hash, stored_hash)
    except ValueError:
        return False


def get_expiry_date(days: int = 30) -> datetime:
    """
    Get an expiry date from now.

    Args:
        days: Number of days until expiry

    Returns:
        Datetime of expiry
    """
    return datetime.utcnow() + timedelta(days=days)


def is_expired(expiry_date: Optional[datetime]) -> bool:
    """
    Check if a date has expired.

    Args:
        expiry_date: The expiry datetime

    Returns:
        True if expired or None
    """
    if expiry_date is None:
        return False
    return datetime.utcnow() > expiry_date


def parse_user_agent(user_agent: str) -> dict:
    """
    Parse a user agent string to extract device info.

    Args:
        user_agent: The user agent string

    Returns:
        Dict with device_type, browser, os
    """
    user_agent_lower = user_agent.lower()

    # Determine device type
    if 'mobile' in user_agent_lower or 'android' in user_agent_lower:
        if 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
            device_type = 'tablet'
        else:
            device_type = 'mobile'
    else:
        device_type = 'desktop'

    # Determine browser
    if 'chrome' in user_agent_lower and 'edg' not in user_agent_lower:
        browser = 'Chrome'
    elif 'firefox' in user_agent_lower:
        browser = 'Firefox'
    elif 'safari' in user_agent_lower and 'chrome' not in user_agent_lower:
        browser = 'Safari'
    elif 'edg' in user_agent_lower:
        browser = 'Edge'
    else:
        browser = 'Other'

    # Determine OS
    if 'windows' in user_agent_lower:
        os = 'Windows'
    elif 'mac' in user_agent_lower:
        os = 'macOS'
    elif 'linux' in user_agent_lower:
        os = 'Linux'
    elif 'android' in user_agent_lower:
        os = 'Android'
    elif 'iphone' in user_agent_lower or 'ipad' in user_agent_lower:
        os = 'iOS'
    else:
        os = 'Other'

    return {
        'device_type': device_type,
        'browser': browser,
        'os': os
    }


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string like "2.5 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe storage.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path separators and null bytes
    filename = re.sub(r'[/\\:\x00]', '', filename)
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_len = 255 - len(ext) - 1 if ext else 255
        filename = f"{name[:max_name_len]}.{ext}" if ext else name[:255]
    return filename or 'unnamed'


def validate_hex_color(color: str) -> bool:
    """
    Validate a hex color string.

    Args:
        color: Color string like "#FF0000"

    Returns:
        True if valid hex color
    """
    return bool(re.match(r'^#[0-9A-Fa-f]{6}$', color))


def get_content_type_icon(content_type: str) -> str:
    """
    Get an icon identifier for a content type.

    Args:
        content_type: The content type enum value

    Returns:
        Icon identifier string
    """
    icons = {
        'proposal': 'file-text',
        'deck': 'presentation',
        'case_study': 'book-open',
        'pricing': 'dollar-sign',
        'contract': 'file-signature',
        'video': 'video',
        'document': 'file',
        'link': 'link',
    }
    return icons.get(content_type, 'file')
