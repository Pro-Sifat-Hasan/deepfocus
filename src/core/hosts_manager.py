"""
Hosts file manager for Windows - handles reading, writing, and backing up hosts file.
Simplified and optimized for reliable blocking/unblocking.
"""
import os
import shutil
import platform
import subprocess
import stat
from pathlib import Path
from typing import List, Set
from datetime import datetime

from ..config.constants import HOSTS_FILE_PATH, HOSTS_BACKUP_PATH, REDIRECT_IP


class HostsManager:
    """Manages Windows hosts file operations."""

    def __init__(self):
        self.hosts_path = Path(HOSTS_FILE_PATH)
        self.backup_dir = Path(HOSTS_BACKUP_PATH)
        self.redirect_ip = REDIRECT_IP
        self._ensure_backup_dir()

    def _ensure_backup_dir(self) -> None:
        """Ensure backup directory exists."""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            pass

    def _flush_dns_cache(self) -> None:
        """Flush DNS cache on Windows for real-time blocking effect."""
        if platform.system() != "Windows":
            return
        try:
            subprocess.run(
                ["ipconfig", "/flushdns"],
                capture_output=True,
                check=False,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        except Exception:
            pass

    def is_admin(self) -> bool:
        """Check if running with administrator privileges."""
        if platform.system() != "Windows":
            return False
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def backup_hosts(self) -> bool:
        """Create a backup of the hosts file."""
        if not self.hosts_path.exists():
            return False
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            # Keep only last 3 backups
            self._cleanup_old_backups(max_backups=3)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"hosts_backup_{timestamp}.txt"
            shutil.copy2(self.hosts_path, backup_file)
            return True
        except (IOError, PermissionError, OSError):
            return True  # Continue even if backup fails

    def _cleanup_old_backups(self, max_backups: int = 3) -> None:
        """Clean up old backup files."""
        try:
            if not self.backup_dir.exists():
                return
            backup_files = sorted(
                self.backup_dir.glob("hosts_backup_*.txt"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            for old_backup in backup_files[max_backups:]:
                try:
                    old_backup.unlink()
                except Exception:
                    pass
        except Exception:
            pass

    def read_hosts(self) -> List[str]:
        """Read the hosts file and return lines."""
        if not self.hosts_path.exists():
            return []
        try:
            with open(self.hosts_path, "r", encoding="utf-8") as f:
                return f.readlines()
        except (IOError, PermissionError):
            return []

    def get_blocked_domains(self) -> Set[str]:
        """Get set of currently blocked domains from hosts file."""
        try:
            lines = self.read_hosts()
            blocked = set()
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2 and parts[0] == self.redirect_ip:
                    for part in parts[1:]:
                        if not part.startswith("#"):
                            blocked.add(part.lower())
            return blocked
        except Exception:
            return set()

    def _make_writable(self) -> bool:
        """Make hosts file writable, return True if was read-only."""
        try:
            if not (self.hosts_path.stat().st_mode & stat.S_IWRITE):
                self.hosts_path.chmod(stat.S_IREAD | stat.S_IWRITE)
                return True
        except Exception:
            pass
        return False

    def _restore_readonly(self, was_readonly: bool) -> None:
        """Restore read-only attribute if it was set."""
        if was_readonly:
            try:
                self.hosts_path.chmod(stat.S_IREAD)
            except Exception:
                pass

    def block_domains(self, domains: List[str], force: bool = False) -> bool:
        """
        Block multiple domains efficiently with proper formatting.
        Each domain gets its own line: 127.0.0.1 domain.com
        
        Args:
            domains: List of domain names to block
            force: If True, re-add domains even if they appear blocked
        """
        if not domains:
            return True

        try:
            # Backup before modification
            self.backup_hosts()
            
            # Read current hosts file
            lines = self.read_hosts()
            
            # Prepare domains to block (lowercase, stripped)
            domains_to_block = set(d.strip().lower() for d in domains if d.strip())
            
            if not domains_to_block:
                return True
            
            # Get existing blocked domains
            existing_blocked = self.get_blocked_domains() if not force else set()
            
            # Filter out already blocked domains (unless force)
            if not force:
                domains_to_block = domains_to_block - existing_blocked
                if not domains_to_block:
                    return True
            
            # Build new file content
            new_lines = []
            marker = "# DeepFocus entries"
            marker_found = False
            
            for line in lines:
                line_stripped = line.strip()
                
                # Check for our marker
                if marker in line:
                    marker_found = True
                    new_lines.append(line)
                    continue
                
                # Check for DeepFocus blocked entries
                if line_stripped.startswith(self.redirect_ip):
                    parts = line.split()
                    if len(parts) >= 2:
                        # Extract domain from this line
                        domain_in_line = parts[1].lower() if len(parts) > 1 else ""
                        
                        # If force mode, remove entries we're about to add
                        if force and domain_in_line in domains_to_block:
                            continue  # Skip - will re-add later
                        
                        # Check for malformed entries (very long or concatenated)
                        if len(domain_in_line) > 60 or domain_in_line.count('.') > 5:
                            continue  # Skip malformed entry
                
                new_lines.append(line)
            
            # Ensure file ends with newline
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines[-1] += '\n'
            
            # Add marker if not present
            if not marker_found:
                new_lines.append(f"\n{marker}\n")
            
            # Add each domain on its own line with explicit newline
            for domain in sorted(domains_to_block):
                entry = f"{self.redirect_ip} {domain}\n"
                new_lines.append(entry)
            
            # Write to hosts file
            was_readonly = self._make_writable()
            
            try:
                with open(self.hosts_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
            finally:
                self._restore_readonly(was_readonly)
            
            # Flush DNS cache for immediate effect
            self._flush_dns_cache()
            
            return True
            
        except PermissionError as e:
            raise PermissionError(
                f"Cannot write to hosts file. Please run as Administrator. Error: {e}"
            )
        except Exception as e:
            raise IOError(f"Failed to block domains: {e}")

    def unblock_domains(self, domains: List[str]) -> bool:
        """
        Unblock multiple domains efficiently.
        
        Args:
            domains: List of domain names to unblock
        """
        if not domains:
            return True

        try:
            # Backup before modification
            self.backup_hosts()
            
            # Read current hosts file
            lines = self.read_hosts()
            
            # Prepare domains to unblock (lowercase, stripped)
            domains_to_unblock = set(d.strip().lower() for d in domains if d.strip())
            
            if not domains_to_unblock:
                return True
            
            # Build new file content, removing specified domains
            new_lines = []
            modified = False
            
            for line in lines:
                line_stripped = line.strip()
                
                # Check for DeepFocus blocked entries
                if line_stripped.startswith(self.redirect_ip):
                    parts = line.split()
                    if len(parts) >= 2:
                        domain_in_line = parts[1].lower() if len(parts) > 1 else ""
                        
                        if domain_in_line in domains_to_unblock:
                            modified = True
                            continue  # Skip this line (remove the block)
                
                new_lines.append(line)
            
            if not modified:
                return True  # Nothing to change
            
            # Write to hosts file
            was_readonly = self._make_writable()
            
            try:
                with open(self.hosts_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
            finally:
                self._restore_readonly(was_readonly)
            
            # Flush DNS cache for immediate effect
            self._flush_dns_cache()
            
            return True
            
        except PermissionError as e:
            raise PermissionError(
                f"Cannot write to hosts file. Please run as Administrator. Error: {e}"
            )
        except Exception as e:
            raise IOError(f"Failed to unblock domains: {e}")

    def block_domain(self, domain: str, force: bool = False) -> bool:
        """Block a single domain."""
        return self.block_domains([domain], force=force)

    def unblock_domain(self, domain: str) -> bool:
        """Unblock a single domain."""
        return self.unblock_domains([domain])

    def restore_backup(self, backup_file: Path) -> bool:
        """Restore hosts file from a backup."""
        if not backup_file.exists():
            return False
        try:
            shutil.copy2(backup_file, self.hosts_path)
            self._flush_dns_cache()
            return True
        except (IOError, PermissionError):
            return False
