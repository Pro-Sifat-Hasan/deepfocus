"""
Unit tests for settings module.
"""
import pytest
import sys
import json
from pathlib import Path
from unittest.mock import patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestSettings:
    """Test settings functionality."""

    def test_default_settings(self):
        """Test default settings values."""
        # Note: This test may modify actual settings.json
        # In production, use a test settings file
        from config.settings import Settings
        
        # Create temporary settings
        settings = Settings()
        
        # Check default values
        assert settings.get_language() in ["en", "bn"]
        assert isinstance(settings.is_auto_start(), bool)

    def test_language_setting(self):
        """Test language setting management."""
        from config.settings import Settings
        settings = Settings()
        
        # Set language
        settings.set_language("bn")
        assert settings.get_language() == "bn"
        
        settings.set_language("en")
        assert settings.get_language() == "en"

    def test_platform_blocked_state(self):
        """Test platform blocked state management."""
        from config.settings import Settings
        settings = Settings()
        
        platform = "facebook"
        
        # Set blocked
        settings.set_platform_blocked(platform, True)
        assert settings.is_platform_blocked(platform) is True
        
        # Set unblocked
        settings.set_platform_blocked(platform, False)
        assert settings.is_platform_blocked(platform) is False
