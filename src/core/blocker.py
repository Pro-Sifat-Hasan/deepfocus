"""
Website blocking engine - manages blocking/unblocking of platforms and domains.
"""
from typing import List, Dict, Set, Tuple, Optional

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

    def block_platform(self, platform: str, force: bool = False) -> bool:
        """Block a platform by blocking all its domains.
        
        Args:
            platform: Platform name to block
            force: If True, force re-blocking even if domains appear blocked (useful after unblocking)
        """
        if platform not in PLATFORM_DOMAINS:
            return False

        domains = PLATFORM_DOMAINS[platform]
        
        try:
            # Always update settings FIRST to ensure persistence
            settings.set_platform_blocked(platform, True)
            
            # Check if platform was recently unblocked - if so, force re-blocking
            blocked_domains = self.hosts_manager.get_blocked_domains()
            any_blocked = any(domain in blocked_domains for domain in domains)
            
            # If settings say blocked but hosts file doesn't, or if force=True, use force
            # ALWAYS use force=True to ensure domains are properly blocked after unblocking
            if force or (not any_blocked):
                success = self.hosts_manager.block_domains(domains, force=True)
            else:
                # Even if some domains appear blocked, verify all are blocked and force if needed
                all_blocked = all(domain in blocked_domains for domain in domains)
                if not all_blocked:
                    success = self.hosts_manager.block_domains(domains, force=True)
                else:
                    success = True
            
            if success:
                # Verify blocking was applied immediately
                blocked_domains_after = self.hosts_manager.get_blocked_domains()
                all_blocked_after = all(domain in blocked_domains_after for domain in domains)
                if not all_blocked_after:
                    # Retry with force to ensure all domains blocked
                    success = self.hosts_manager.block_domains(domains, force=True)
                    settings.set_platform_blocked(platform, True)
            else:
                # Still persist settings - blocking will apply on next admin run
                settings.set_platform_blocked(platform, True)
            
            return success
        except Exception:
            # Ensure settings persist even on error
            settings.set_platform_blocked(platform, True)
            return False

    def unblock_platform(self, platform: str) -> bool:
        """Unblock a platform by unblocking all its domains."""
        if platform not in PLATFORM_DOMAINS:
            return False

        domains = PLATFORM_DOMAINS[platform]
        success = self.hosts_manager.unblock_domains(domains)
        
        if success:
            # Update settings - remember it was unblocked
            settings.set_platform_blocked(platform, False)
            # Flush DNS cache immediately after unblocking for real-time effect
            self.hosts_manager._flush_dns_cache()
        else:
            # Still update settings even if hosts file update failed
            settings.set_platform_blocked(platform, False)
        
        return success

    def is_platform_blocked(self, platform: str) -> bool:
        """Check if a platform is currently blocked."""
        if platform not in PLATFORM_DOMAINS:
            return False

        domains = PLATFORM_DOMAINS[platform]
        blocked_domains = self.hosts_manager.get_blocked_domains()
        
        # Check if at least one domain is blocked in hosts file
        is_blocked_in_hosts = any(domain in blocked_domains for domain in domains)
        
        # Also check settings
        is_blocked_in_settings = settings.is_platform_blocked(platform)
        
        # If settings say blocked but hosts file doesn't, try to apply
        if is_blocked_in_settings and not is_blocked_in_hosts:
            if self.is_admin():
                try:
                    self.hosts_manager.block_domains(domains)
                    # Re-check after applying
                    blocked_domains = self.hosts_manager.get_blocked_domains()
                    return any(domain in blocked_domains for domain in domains)
                except:
                    pass
            # Return settings value if can't apply
            return is_blocked_in_settings
        
        return is_blocked_in_hosts

    def toggle_platform(self, platform: str) -> bool:
        """Toggle platform block/unblock state."""
        if self.is_platform_blocked(platform):
            return self.unblock_platform(platform)
        else:
            return self.block_platform(platform)

    def block_adult_content(self) -> bool:
        """Block adult content domains - optimized batch write for real-time blocking."""
        # Use force=True to ensure all domains are blocked and clean up malformed entries
        success = self.hosts_manager.block_domains(ADULT_CONTENT_DOMAINS, force=True)
        
        if success:
            settings.set_adult_content_blocked(True)
        
        return success

    def unblock_adult_content(self) -> bool:
        """Unblock adult content domains."""
        success = self.hosts_manager.unblock_domains(ADULT_CONTENT_DOMAINS)
        
        if success:
            settings.set_adult_content_blocked(False)
        
        return success

    def toggle_adult_content(self) -> bool:
        """Toggle adult content blocking."""
        if settings.is_adult_content_blocked():
            return self.unblock_adult_content()
        else:
            return self.block_adult_content()
    
    def block_casino_gambling(self) -> bool:
        """Block casino/gambling domains - optimized for real-time blocking."""
        # Use force=True to ensure all domains are blocked and clean up malformed entries
        success = self.hosts_manager.block_domains(CASINO_GAMBLING_DOMAINS, force=True)
        
        if success:
            settings.set_casino_gambling_blocked(True)
            # Immediate DNS cache flush for real-time effect
            self.hosts_manager._flush_dns_cache()
        
        return success
    
    def unblock_casino_gambling(self) -> bool:
        """Unblock casino/gambling domains."""
        success = self.hosts_manager.unblock_domains(CASINO_GAMBLING_DOMAINS)
        
        if success:
            settings.set_casino_gambling_blocked(False)
        
        return success
    
    def toggle_casino_gambling(self) -> bool:
        """Toggle casino/gambling blocking."""
        if settings.is_casino_gambling_blocked():
            return self.unblock_casino_gambling()
        else:
            return self.block_casino_gambling()

    def block_custom_domain(self, domain: str) -> Tuple[bool, Optional[str]]:
        """
        Block a custom domain and its variations (www, root domain, subdomains).
        
        Returns:
            Tuple of (success, error_message)
        """
        # Sanitize domain
        domain = sanitize_domain(domain)
        
        # Validate domain
        is_valid, error_msg = validate_domain(domain)
        if not is_valid:
            return False, error_msg

        # Check if already blocked
        blocked_domains = self.hosts_manager.get_blocked_domains()
        if domain in blocked_domains:
            return True, None

        # Add to custom domains list
        settings.add_custom_domain(domain)

        # Block the domain and its variations to ensure all paths/subdomains are blocked
        domains_to_block = self._get_domain_variations(domain)
        # Use force=True to clean up any malformed entries and ensure proper blocking
        success = self.hosts_manager.block_domains(domains_to_block, force=True)
        
        if not success:
            settings.remove_custom_domain(domain)
            return False, "Failed to block domain. Please run as administrator."

        # DNS cache already flushed by block_domains
        
        return True, None
    
    def _get_domain_variations(self, domain: str) -> List[str]:
        """
        Get all domain variations to block (domain, www.domain, root domain).
        This ensures all paths and subdomains are blocked at DNS level.
        
        IMPORTANT: Hosts file blocks at DNS level, so blocking a domain blocks ALL paths.
        For example: blocking 'example.com' blocks 'example.com/any/path'
        
        Args:
            domain: The domain to get variations for
            
        Returns:
            List of domain variations to block
        """
        variations = [domain]  # Always block the exact domain
        
        # Add www version if not already present
        if not domain.startswith('www.'):
            variations.append(f"www.{domain}")
        
        # Extract root domain to block all subdomains
        # For app.todoist.com -> also block todoist.com (blocks ALL *.todoist.com)
        parts = domain.split('.')
        if len(parts) > 2:
            # Get root domain (last two parts: domain.tld)
            root_domain = '.'.join(parts[-2:])  # e.g., todoist.com from app.todoist.com
            if root_domain != domain and root_domain not in variations:
                variations.append(root_domain)
                # Also add www version of root domain
                variations.append(f"www.{root_domain}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for d in variations:
            d_clean = d.lower().strip()
            if d_clean and d_clean not in seen:
                seen.add(d_clean)
                unique_variations.append(d_clean)
        
        return unique_variations

    def unblock_custom_domain(self, domain: str) -> bool:
        """Unblock a custom domain."""
        success = self.hosts_manager.unblock_domain(domain)
        
        if success:
            settings.remove_custom_domain(domain)
        
        return success

    def get_custom_domains(self) -> List[str]:
        """Get list of custom domains."""
        return settings.get_custom_domains()

    def get_all_blocked_domains(self) -> Set[str]:
        """Get all currently blocked domains."""
        return self.hosts_manager.get_blocked_domains()

    def sync_with_hosts_file(self) -> None:
        """Sync settings with hosts file and apply blocking/unblocking based on settings.
        This ensures settings persist after computer restart."""
        if not self.is_admin():
            return
        
        blocked_domains = self.hosts_manager.get_blocked_domains()
        
        # For each platform: sync settings with hosts file
        for platform, domains in PLATFORM_DOMAINS.items():
            is_blocked_in_settings = settings.is_platform_blocked(platform)
            is_blocked_in_hosts = any(domain in blocked_domains for domain in domains)
            all_blocked_in_hosts = all(domain in blocked_domains for domain in domains)
            
            # If settings say blocked but hosts file doesn't, apply blocking
            if is_blocked_in_settings and not all_blocked_in_hosts:
                try:
                    # Use force=True to ensure all domains are properly blocked
                    success = self.hosts_manager.block_domains(domains, force=True)
                    if success:
                        settings.set_platform_blocked(platform, True)
                    else:
                        settings.set_platform_blocked(platform, True)
                except Exception:
                    settings.set_platform_blocked(platform, True)
            # If settings say unblocked but hosts file still has domains, unblock them
            elif not is_blocked_in_settings and is_blocked_in_hosts:
                try:
                    success = self.hosts_manager.unblock_domains(domains)
                    if success:
                        # Flush DNS cache immediately after unblocking
                        self.hosts_manager._flush_dns_cache()
                except Exception:
                    pass
            # If hosts file matches settings, ensure settings are persisted
            elif all_blocked_in_hosts and is_blocked_in_settings:
                settings.set_platform_blocked(platform, True)
            elif all_blocked_in_hosts and not is_blocked_in_settings:
                # Hosts file says blocked but settings say unblocked - update settings to match hosts
                settings.set_platform_blocked(platform, True)
        
        # Apply adult content blocking if settings say blocked but hosts file doesn't
        if settings.is_adult_content_blocked():
            blocked_count = sum(1 for domain in ADULT_CONTENT_DOMAINS if domain in blocked_domains)
            needs_blocking = blocked_count < (len(ADULT_CONTENT_DOMAINS) * 0.8)
            if needs_blocking:
                try:
                    self.hosts_manager.block_domains(ADULT_CONTENT_DOMAINS, force=True)
                except Exception:
                    pass
        
        # Apply casino/gambling blocking if settings say blocked but hosts file doesn't
        if settings.is_casino_gambling_blocked():
            blocked_count = sum(1 for domain in CASINO_GAMBLING_DOMAINS if domain in blocked_domains)
            needs_blocking = blocked_count < (len(CASINO_GAMBLING_DOMAINS) * 0.8)
            if needs_blocking:
                try:
                    self.hosts_manager.block_domains(CASINO_GAMBLING_DOMAINS, force=True)
                except Exception:
                    pass
