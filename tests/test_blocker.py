"""
Unit tests for blocker module.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestBlocker:
    """Test blocker functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        from core.blocker import Blocker
        self.blocker = Blocker()

    def test_initialization(self):
        """Test Blocker initialization."""
        assert self.blocker.hosts_manager is not None

    def test_is_admin_returns_boolean(self):
        """Test is_admin returns boolean."""
        result = self.blocker.is_admin()
        assert isinstance(result, bool)

    def test_is_platform_blocked_returns_boolean(self):
        """Test is_platform_blocked returns boolean."""
        result = self.blocker.is_platform_blocked("facebook")
        assert isinstance(result, bool)

    def test_unknown_platform_returns_false(self):
        """Test unknown platform returns False."""
        result = self.blocker.is_platform_blocked("unknown_platform_xyz")
        assert result is False

    def test_block_platform_unknown(self):
        """Test blocking unknown platform returns error."""
        success, error = self.blocker.block_platform("unknown_platform_xyz")
        assert success is False
        assert error is not None

    def test_unblock_platform_unknown(self):
        """Test unblocking unknown platform returns error."""
        success, error = self.blocker.unblock_platform("unknown_platform_xyz")
        assert success is False
        assert error is not None

    def test_get_custom_domains_returns_list(self):
        """Test get_custom_domains returns list."""
        result = self.blocker.get_custom_domains()
        assert isinstance(result, list)

    def test_get_all_blocked_domains_returns_set(self):
        """Test get_all_blocked_domains returns set."""
        result = self.blocker.get_all_blocked_domains()
        assert isinstance(result, set)


class TestBlockerDomainVariations:
    """Test domain variation generation."""

    def setup_method(self):
        """Setup test fixtures."""
        from core.blocker import Blocker
        self.blocker = Blocker()

    def test_get_domain_variations(self):
        """Test domain variations include www prefix."""
        variations = self.blocker._get_domain_variations("example.com")
        assert "example.com" in variations
        assert "www.example.com" in variations

    def test_get_domain_variations_already_www(self):
        """Test domain variations when already has www."""
        variations = self.blocker._get_domain_variations("www.example.com")
        assert "www.example.com" in variations
        # Should not add www.www.example.com
        assert len(variations) == 1


class TestBlockerConstants:
    """Test blocker works with constants."""

    def test_platform_domains_exist(self):
        """Test platform domains are defined."""
        from config.constants import PLATFORM_DOMAINS
        assert "facebook" in PLATFORM_DOMAINS
        assert "instagram" in PLATFORM_DOMAINS
        assert "linkedin" in PLATFORM_DOMAINS
        assert "twitter" in PLATFORM_DOMAINS

    def test_platform_domains_have_entries(self):
        """Test each platform has domains."""
        from config.constants import PLATFORM_DOMAINS
        for platform, domains in PLATFORM_DOMAINS.items():
            assert len(domains) > 0, f"{platform} should have domains"
