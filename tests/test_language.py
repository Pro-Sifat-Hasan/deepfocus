"""
Unit tests for language module.
"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestLanguageManager:
    """Test language translation functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        from utils.language import LanguageManager
        self.lang = LanguageManager()

    def test_initialization(self):
        """Test LanguageManager initialization."""
        assert "en" in self.lang.translations
        assert "bn" in self.lang.translations

    def test_translate_english(self):
        """Test English translation."""
        self.lang.set_language("en")
        result = self.lang.translate("login_title")
        assert result == "DeepFocus Login"

    def test_translate_bengali(self):
        """Test Bengali translation."""
        self.lang.set_language("bn")
        result = self.lang.translate("login_title")
        assert "DeepFocus" in result
        assert "লগইন" in result

    def test_translate_missing_key(self):
        """Test missing translation key returns key."""
        result = self.lang.translate("nonexistent_key_xyz")
        assert result == "nonexistent_key_xyz"

    def test_translate_with_kwargs(self):
        """Test translation with format parameters."""
        self.lang.set_language("en")
        result = self.lang.translate("password_for_platform", platform="Facebook")
        assert "Facebook" in result

    def test_get_current_language(self):
        """Test get current language."""
        result = self.lang.get_current_language()
        assert result in ["en", "bn"]

    def test_set_language(self):
        """Test set language."""
        self.lang.set_language("bn")
        assert self.lang.get_current_language() == "bn"
        
        self.lang.set_language("en")
        assert self.lang.get_current_language() == "en"

    def test_get_alias(self):
        """Test get method as alias."""
        self.lang.set_language("en")
        result = self.lang.get("login_button")
        assert result == "Login"

    def test_platform_names_exist(self):
        """Test platform name translations exist."""
        platforms = ["facebook", "instagram", "linkedin", "twitter", "youtube", "tiktok", "reddit", "snapchat"]
        
        for platform in platforms:
            result = self.lang.translate(platform)
            assert result != platform, f"Missing translation for {platform}"
