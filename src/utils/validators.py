"""
Input validation utilities.
"""
import re
from typing import Tuple, Optional


def validate_domain(domain: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a domain name.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not domain:
        return False, "Domain cannot be empty"

    domain = domain.strip().lower()

    # Basic domain validation regex
    domain_pattern = re.compile(
        r'^([a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$'
    )

    if not domain_pattern.match(domain):
        return False, "Invalid domain format"

    # Check for common invalid patterns
    if domain.startswith('.') or domain.endswith('.'):
        return False, "Domain cannot start or end with a dot"

    if '..' in domain:
        return False, "Domain cannot contain consecutive dots"

    if len(domain) > 253:
        return False, "Domain name too long (max 253 characters)"

    # Check for localhost or IP address
    if domain.startswith('127.') or domain.startswith('localhost'):
        return False, "Cannot block localhost or IP addresses"

    return True, None


def validate_password(password: str, min_length: int = 4) -> Tuple[bool, Optional[str]]:
    """
    Validate a password.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password cannot be empty"

    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters"

    if len(password) > 128:
        return False, "Password too long (max 128 characters)"

    return True, None


def sanitize_domain(domain: str) -> str:
    """Sanitize domain input by removing protocol and paths."""
    domain = domain.strip().lower()
    
    # Remove protocol
    domain = re.sub(r'^https?://', '', domain)
    domain = re.sub(r'^www\.', '', domain)
    
    # Remove path
    domain = domain.split('/')[0]
    domain = domain.split('?')[0]
    domain = domain.split('#')[0]
    
    # Remove port
    domain = domain.split(':')[0]
    
    return domain.strip()
