"""
Unit tests for hosts_manager module.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestHostsManager:
    """Test hosts file management functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        from core.hosts_manager import HostsManager
        self.hosts_manager = HostsManager()

    def test_initialization(self):
        """Test HostsManager initialization."""
        assert self.hosts_manager.redirect_ip == "127.0.0.1"
        assert self.hosts_manager.hosts_path is not None

    def test_get_blocked_domains_returns_set(self):
        """Test get_blocked_domains returns set."""
        result = self.hosts_manager.get_blocked_domains()
        assert isinstance(result, set)

    def test_is_admin_returns_boolean(self):
        """Test is_admin returns boolean."""
        result = self.hosts_manager.is_admin()
        assert isinstance(result, bool)

    def test_read_hosts_returns_list(self):
        """Test read_hosts returns list."""
        result = self.hosts_manager.read_hosts()
        assert isinstance(result, list)


class TestHostsManagerBackup:
    """Test backup functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        from core.hosts_manager import HostsManager
        self.hosts_manager = HostsManager()

    def test_backup_dir_creation(self):
        """Test backup directory creation doesn't raise."""
        self.hosts_manager._ensure_backup_dir()
        # Should not raise

    def test_backup_hosts_returns_boolean(self):
        """Test backup_hosts returns boolean."""
        result = self.hosts_manager.backup_hosts()
        assert isinstance(result, bool)
