"""
Unit tests for system_integration module.
"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestSystemIntegration:
    """Test system integration functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        from utils.system_integration import SystemIntegration
        self.integration = SystemIntegration()

    def test_initialization(self):
        """Test SystemIntegration initialization."""
        assert self.integration.is_windows is not None

    def test_check_admin_privileges_returns_boolean(self):
        """Test check_admin_privileges returns boolean."""
        result = self.integration.check_admin_privileges()
        assert isinstance(result, bool)

    def test_get_app_path_returns_string(self):
        """Test get_app_path returns string."""
        result = self.integration.get_app_path()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_is_auto_start_enabled_returns_boolean(self):
        """Test is_auto_start_enabled returns boolean."""
        result = self.integration.is_auto_start_enabled()
        assert isinstance(result, bool)


class TestStopTrayIcon:
    """Test stop_tray_icon cleanup function."""

    def test_stop_tray_icon_no_error(self):
        """Test stop_tray_icon doesn't raise when no icon exists."""
        from utils.system_integration import stop_tray_icon
        # Should not raise
        stop_tray_icon()
