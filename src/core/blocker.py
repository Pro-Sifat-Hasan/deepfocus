"""
Website blocking engine - manages blocking/unblocking of platforms and domains.
Simplified and optimized version.
"""
from typing import List, Set, Tuple, Optional

from ..config.constants import PLATFORM_DOMAINS, ADULT_CONTENT_DOMAINS, CASINO_GAMBLING_DOMAINS
from ..config.settings import settings
from ..core.hosts_manager import HostsManager
from ..utils.validators import validate_domain, sanitize_domain


class Blocker:
    """Manages website blocking operations."""

    def __init__(self):
        self.hosts_manager = HostsManager()

    def is_admin(self) -> bool:
        """Check if running with administrator privileges."""
        return self.hosts_manager.is_admin()

    def block_platform(self, platform: str, force: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Block a platform by blocking all its domains.
        
        Returns:
            Tuple of (success, error_message)
        """
        if platform not in PLATFORM_DOMAINS:
            return False, f"Unknown platform: {platform}"

        domains = PLATFORM_DOMAINS[platform]
        
        try:
            success = self.hosts_manager.block_domains(domains, force=force)
            if success:
                settings.set_platform_blocked(platform, True)
                return True, None
            else:
                settings.set_platform_blocked(platform, True)  # Save intent
                return False, "Failed to apply blocking"
        except PermissionError as e:
            settings.set_platform_blocked(platform, True)  # Save intent
            return False, str(e)
        except Exception as e:
            settings.set_platform_blocked(platform, True)  # Save intent
            return False, f"Error blocking platform: {e}"

    def unblock_platform(self, platform: str) -> Tuple[bool, Optional[str]]:
        """
        Unblock a platform by unblocking all its domains.
        
        Returns:
            Tuple of (success, error_message)
        """
        if platform not in PLATFORM_DOMAINS:
            return False, f"Unknown platform: {platform}"

        domains = PLATFORM_DOMAINS[platform]
        
        try:
            success = self.hosts_manager.unblock_domains(domains)
            settings.set_platform_blocked(platform, False)
            if success:
                return True, None
            else:
                return False, "Failed to apply unblocking"
        except PermissionError as e:
            settings.set_platform_blocked(platform, False)  # Save intent
            return False, str(e)
        except Exception as e:
            settings.set_platform_blocked(platform, False)  # Save intent
            return False, f"Error unblocking platform: {e}"

    def is_platform_blocked(self, platform: str) -> bool:
        """Check if a platform is currently blocked."""
        if platform not in PLATFORM_DOMAINS:
            return False
        
        # Use settings as source of truth
        return settings.is_platform_blocked(platform)

    def toggle_platform(self, platform: str) -> Tuple[bool, Optional[str]]:
        """Toggle platform block/unblock state."""
        if self.is_platform_blocked(platform):
            return self.unblock_platform(platform)
        else:
            return self.block_platform(platform)

    def block_adult_content(self) -> Tuple[bool, Optional[str]]:
        """Block adult content domains."""
        try:
            success = self.hosts_manager.block_domains(ADULT_CONTENT_DOMAINS, force=True)
            if success:
                settings.set_adult_content_blocked(True)
                return True, None
            else:
                return False, "Failed to block adult content"
        except Exception as e:
            return False, str(e)

    def unblock_adult_content(self) -> Tuple[bool, Optional[str]]:
        """Unblock adult content domains."""
        try:
            success = self.hosts_manager.unblock_domains(ADULT_CONTENT_DOMAINS)
            settings.set_adult_content_blocked(False)
            return success, None if success else "Failed to unblock"
        except Exception as e:
            return False, str(e)

    def toggle_adult_content(self) -> Tuple[bool, Optional[str]]:
        """Toggle adult content blocking."""
        if settings.is_adult_content_blocked():
            return self.unblock_adult_content()
        else:
            return self.block_adult_content()

    def block_casino_gambling(self) -> Tuple[bool, Optional[str]]:
        """Block casino/gambling domains."""
        try:
            success = self.hosts_manager.block_domains(CASINO_GAMBLING_DOMAINS, force=True)
            if success:
                settings.set_casino_gambling_blocked(True)
                return True, None
            else:
                return False, "Failed to block casino/gambling sites"
        except Exception as e:
            return False, str(e)

    def unblock_casino_gambling(self) -> Tuple[bool, Optional[str]]:
        """Unblock casino/gambling domains."""
        try:
            success = self.hosts_manager.unblock_domains(CASINO_GAMBLING_DOMAINS)
            settings.set_casino_gambling_blocked(False)
            return success, None if success else "Failed to unblock"
        except Exception as e:
            return False, str(e)

    def toggle_casino_gambling(self) -> Tuple[bool, Optional[str]]:
        """Toggle casino/gambling blocking."""
        if settings.is_casino_gambling_blocked():
            return self.unblock_casino_gambling()
        else:
            return self.block_casino_gambling()

    def block_custom_domain(self, domain: str) -> Tuple[bool, Optional[str]]:
        """Block a custom domain and its variations."""
        domain = sanitize_domain(domain)
        
        is_valid, error_msg = validate_domain(domain)
        if not is_valid:
            return False, error_msg

        # Get domain variations (with www prefix)
        domains_to_block = self._get_domain_variations(domain)
        
        try:
            success = self.hosts_manager.block_domains(domains_to_block, force=True)
            if success:
                settings.add_custom_domain(domain)
                return True, None
            else:
                return False, "Failed to block domain"
        except PermissionError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Error: {e}"

    def _get_domain_variations(self, domain: str) -> List[str]:
        """Get domain variations to block (domain + www.domain)."""
        variations = [domain]
        if not domain.startswith('www.'):
            variations.append(f"www.{domain}")
        return variations

    def unblock_custom_domain(self, domain: str) -> Tuple[bool, Optional[str]]:
        """Unblock a custom domain."""
        domains_to_unblock = self._get_domain_variations(domain)
        
        try:
            success = self.hosts_manager.unblock_domains(domains_to_unblock)
            if success:
                settings.remove_custom_domain(domain)
                return True, None
            else:
                return False, "Failed to unblock domain"
        except Exception as e:
            return False, str(e)

    def get_custom_domains(self) -> List[str]:
        """Get list of custom domains."""
        return settings.get_custom_domains()

    def get_all_blocked_domains(self) -> Set[str]:
        """Get all currently blocked domains."""
        return self.hosts_manager.get_blocked_domains()

    def sync_with_hosts_file(self) -> None:
        """
        Sync settings with hosts file.
        Apply blocking for platforms that should be blocked,
        unblock platforms that should be unblocked.
        """
        if not self.is_admin():
            return

        # Sync each platform
        for platform, domains in PLATFORM_DOMAINS.items():
            should_be_blocked = settings.is_platform_blocked(platform)
            
            try:
                if should_be_blocked:
                    self.hosts_manager.block_domains(domains, force=True)
                else:
                    self.hosts_manager.unblock_domains(domains)
            except Exception:
                pass  # Continue with other platforms

        # Sync adult content
        if settings.is_adult_content_blocked():
            try:
                self.hosts_manager.block_domains(ADULT_CONTENT_DOMAINS, force=True)
            except Exception:
                pass

        # Sync casino/gambling
        if settings.is_casino_gambling_blocked():
            try:
                self.hosts_manager.block_domains(CASINO_GAMBLING_DOMAINS, force=True)
            except Exception:
                pass
