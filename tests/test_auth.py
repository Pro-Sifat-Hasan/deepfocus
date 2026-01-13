"""
Unit tests for authentication module.
"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestAuth:
    """Test authentication functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        from core.auth import Auth
        from config.constants import DEFAULT_PASSWORD
        self.auth = Auth()
        self.DEFAULT_PASSWORD = DEFAULT_PASSWORD

    def test_verify_default_password(self):
        """Test verification of default password."""
        # Initialize password
        self.auth.initialize_main_password()
        
        # Should verify correctly
        assert self.auth.verify_main_password(self.DEFAULT_PASSWORD) is True
        assert self.auth.verify_main_password("wrong_password") is False

    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password"
        password_hash = self.auth._hash_password(password)
        
        # Hash should be different from original
        assert password_hash != password
        
        # Should be able to verify
        assert self.auth._verify_password(password, password_hash) is True
        assert self.auth._verify_password("wrong", password_hash) is False

    def test_change_main_password(self):
        """Test changing main password."""
        self.auth.initialize_main_password()
        
        # Change password
        new_password = "new_password123"
        success = self.auth.change_main_password(self.DEFAULT_PASSWORD, new_password)
        
        assert success is True
        
        # Old password should not work
        assert self.auth.verify_main_password(self.DEFAULT_PASSWORD) is False
        
        # New password should work
        assert self.auth.verify_main_password(new_password) is True

    def test_platform_password(self):
        """Test platform password management."""
        platform = "facebook"
        password = "platform_pass"
        
        # Set password
        success = self.auth.set_platform_password(platform, password)
        assert success is True
        
        # Should have password
        assert self.auth.has_platform_password(platform) is True
        
        # Should verify correctly
        assert self.auth.verify_platform_password(platform, password) is True
        assert self.auth.verify_platform_password(platform, "wrong") is False
        
        # Remove password
        self.auth.remove_platform_password(platform)
        assert self.auth.has_platform_password(platform) is False
        # Should allow access when no password set
        assert self.auth.verify_platform_password(platform, "") is True
