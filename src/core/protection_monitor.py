"""
Advanced protection monitor - prevents manual hosts file editing and re-applies blocks.
"""
import threading
import time
from typing import Set
from pathlib import Path

from ..config.constants import PLATFORM_DOMAINS, ADULT_CONTENT_DOMAINS
from ..config.settings import settings
from .hosts_manager import HostsManager


class ProtectionMonitor:
    """Monitors hosts file and re-applies blocks if manually removed."""
    
    def __init__(self):
        self.hosts_manager = HostsManager()
        self.running = False
        self.monitor_thread = None
        self.check_interval = 30  # Check every 30 seconds
        self.last_hosts_content = None
        
    def start(self) -> None:
        """Start the protection monitor."""
        if self.running:
            return
        
        if not self.hosts_manager.is_admin():
            print("Protection monitor: Not running as admin - monitor disabled")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("Protection monitor: Started (checking every 30 seconds)")
    
    def stop(self) -> None:
        """Stop the protection monitor."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("Protection monitor: Stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        # Wait a bit before starting checks
        time.sleep(5)
        
        while self.running:
            try:
                if self.hosts_manager.is_admin():
                    self._check_and_reapply_blocks()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"Protection monitor error: {e}")
                time.sleep(self.check_interval)
    
    def _check_and_reapply_blocks(self) -> None:
        """Check hosts file and re-apply blocks if needed, but respect unblocked platforms."""
        try:
            # Get current blocked domains from hosts file
            current_blocked = self.hosts_manager.get_blocked_domains()
            
            # Check platforms - only re-apply if settings say they should be blocked
            for platform, domains in PLATFORM_DOMAINS.items():
                if settings.is_platform_blocked(platform):
                    # Only re-apply if platform should be blocked in settings
                    missing_domains = [d for d in domains if d not in current_blocked]
                    if missing_domains:
                        print(f"Protection monitor: {platform} domains removed! Re-applying blocks...")
                        try:
                            # Force re-block the missing domains
                            for domain in missing_domains:
                                self.hosts_manager.block_domain(domain, force=True)
                            print(f"Protection monitor: Re-applied blocks for {platform}")
                        except Exception as e:
                            print(f"Protection monitor: Failed to re-apply {platform}: {e}")
                else:
                    # Platform should be unblocked - ensure it stays unblocked
                    blocked_domains_for_platform = [d for d in domains if d in current_blocked]
                    if blocked_domains_for_platform:
                        print(f"Protection monitor: {platform} should be unblocked but domains found in hosts file. Unblocking...")
                        try:
                            self.hosts_manager.unblock_domains(blocked_domains_for_platform)
                            print(f"Protection monitor: Unblocked {platform}")
                            self.hosts_manager._flush_dns_cache()
                        except Exception as e:
                            print(f"Protection monitor: Failed to unblock {platform}: {e}")
            
            # Check adult content
            if settings.is_adult_content_blocked():
                missing_adult = [d for d in ADULT_CONTENT_DOMAINS if d not in current_blocked]
                if missing_adult:
                    print(f"Protection monitor: Adult content domains removed! Re-applying blocks...")
                    try:
                        for domain in missing_adult[:5]:  # Re-apply first 5 to avoid spam
                            self.hosts_manager.block_domain(domain, force=True)
                        print("Protection monitor: Re-applied adult content blocks")
                    except Exception as e:
                        print(f"Protection monitor: Failed to re-apply adult content: {e}")
            else:
                # Adult content should be unblocked - ensure it stays unblocked
                blocked_adult = [d for d in ADULT_CONTENT_DOMAINS if d in current_blocked]
                if blocked_adult:
                    print(f"Protection monitor: Adult content should be unblocked but domains found. Unblocking...")
                    try:
                        self.hosts_manager.unblock_domains(blocked_adult[:10])  # Unblock in batches
                        self.hosts_manager._flush_dns_cache()
                    except Exception as e:
                        print(f"Protection monitor: Failed to unblock adult content: {e}")
                        
        except Exception as e:
            print(f"Protection monitor: Error checking blocks: {e}")
    
    def protect_hosts_file(self) -> bool:
        """Make hosts file read-only to prevent manual editing (except for our app).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.hosts_manager.is_admin():
                return False
            
            import os
            import stat
            from pathlib import Path
            
            hosts_path = self.hosts_manager.hosts_path
            
            if not hosts_path.exists():
                return False
            
            # Make file read-only
            current_permissions = hosts_path.stat().st_mode
            hosts_path.chmod(stat.S_IREAD)  # Read-only
            
            print("Protection monitor: Hosts file set to read-only")
            
            # Note: Our app needs to temporarily make it writable when modifying
            # This is handled in hosts_manager
            
            return True
        except Exception as e:
            print(f"Error protecting hosts file: {e}")
            return False
    
    def _unprotect_hosts_file_for_write(self) -> bool:
        """Temporarily make hosts file writable for our app."""
        try:
            import stat
            hosts_path = self.hosts_manager.hosts_path
            if hosts_path.exists():
                hosts_path.chmod(stat.S_IREAD | stat.S_IWRITE)
                return True
        except Exception as e:
            print(f"Error unprotecting hosts file: {e}")
        return False
    
    def _reprotect_hosts_file(self) -> bool:
        """Make hosts file read-only again after write."""
        try:
            import stat
            hosts_path = self.hosts_manager.hosts_path
            if hosts_path.exists():
                hosts_path.chmod(stat.S_IREAD)
                return True
        except Exception as e:
            print(f"Error reprotecting hosts file: {e}")
        return False


# Global monitor instance
protection_monitor = ProtectionMonitor()
