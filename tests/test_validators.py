"""
Unit tests for validators module.
"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.validators import validate_domain, sanitize_domain, validate_password


class TestValidators:
    """Test validation functions."""

    def test_validate_domain_valid(self):
        """Test validation of valid domains."""
        valid_domains = [
            "example.com",
            "subdomain.example.com",
            "test.co.uk",
            "my-site.org",
        ]
        
        for domain in valid_domains:
            is_valid, error = validate_domain(domain)
            assert is_valid is True, f"Domain {domain} should be valid"

    def test_validate_domain_invalid(self):
        """Test validation of invalid domains."""
        invalid_domains = [
            "",
            "invalid",
            ".com",
            "example.",
            "example..com",
            "127.0.0.1",
            "localhost",
        ]
        
        for domain in invalid_domains:
            is_valid, error = validate_domain(domain)
            assert is_valid is False, f"Domain {domain} should be invalid"

    def test_sanitize_domain(self):
        """Test domain sanitization."""
        test_cases = [
            ("https://example.com/path", "example.com"),
            ("http://www.example.com", "example.com"),
            ("www.example.com", "example.com"),
            ("example.com:8080", "example.com"),
            ("example.com/path?query=1", "example.com"),
            ("EXAMPLE.COM", "example.com"),
        ]
        
        for input_domain, expected in test_cases:
            result = sanitize_domain(input_domain)
            assert result == expected, f"Expected {expected}, got {result}"

    def test_validate_password(self):
        """Test password validation."""
        # Valid passwords
        assert validate_password("password123")[0] is True
        assert validate_password("1234")[0] is True  # min length 4
        
        # Invalid passwords
        assert validate_password("")[0] is False
        assert validate_password("123")[0] is False  # too short
        assert validate_password("a" * 129)[0] is False  # too long
