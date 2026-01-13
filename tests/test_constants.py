"""
Unit tests for constants module.
"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.constants import (
    PLATFORM_DOMAINS,
    ADULT_CONTENT_DOMAINS,
    CASINO_GAMBLING_DOMAINS,
    HOSTS_FILE_PATH,
    REDIRECT_IP,
    DEFAULT_PASSWORD
)


class TestConstants:
    """Test constant values."""

    def test_platform_domains_exist(self):
        """Test all expected platforms exist."""
        expected_platforms = [
            "facebook", "instagram", "linkedin", "twitter",
            "youtube", "tiktok", "reddit", "snapchat"
        ]
        
        for platform in expected_platforms:
            assert platform in PLATFORM_DOMAINS, f"Missing platform: {platform}"

    def test_platform_domains_have_entries(self):
        """Test each platform has domain entries."""
        for platform, domains in PLATFORM_DOMAINS.items():
            assert isinstance(domains, list), f"{platform} domains should be list"
            assert len(domains) > 0, f"{platform} should have at least one domain"

    def test_facebook_has_correct_domains(self):
        """Test Facebook domains include main site."""
        assert "facebook.com" in PLATFORM_DOMAINS["facebook"]
        assert "www.facebook.com" in PLATFORM_DOMAINS["facebook"]

    def test_instagram_has_correct_domains(self):
        """Test Instagram domains include main site."""
        assert "instagram.com" in PLATFORM_DOMAINS["instagram"]

    def test_adult_content_domains_exist(self):
        """Test adult content domains list exists."""
        assert isinstance(ADULT_CONTENT_DOMAINS, list)
        assert len(ADULT_CONTENT_DOMAINS) > 0

    def test_casino_gambling_domains_exist(self):
        """Test casino/gambling domains list exists."""
        assert isinstance(CASINO_GAMBLING_DOMAINS, list)
        assert len(CASINO_GAMBLING_DOMAINS) > 0

    def test_hosts_file_path(self):
        """Test hosts file path is correct."""
        assert "hosts" in HOSTS_FILE_PATH.lower()
        assert "drivers" in HOSTS_FILE_PATH.lower()

    def test_redirect_ip(self):
        """Test redirect IP is localhost."""
        assert REDIRECT_IP == "127.0.0.1"

    def test_default_password_exists(self):
        """Test default password is set."""
        assert DEFAULT_PASSWORD is not None
        assert len(DEFAULT_PASSWORD) > 0
