"""
Hosts file manager for Windows - handles reading, writing, and backing up hosts file.
"""
import os
import shutil
import platform
import subprocess
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
        self.last_backup_time = None
        self.last_backup_size = None
        self._ensure_backup_dir()

    def _ensure_backup_dir(self) -> None:
        """Ensure backup directory exists."""
        self.backup_dir.mkdir(exist_ok=True)
    
    def _flush_dns_cache(self) -> None:
        """Flush DNS cache on Windows - optimized single method for performance."""
        if platform.system() == "Windows":
            try:
                # Single fast DNS cache flush - most reliable and fastest
                subprocess.run(
                    ["ipconfig", "/flushdns"], 
                    capture_output=True, 
                    check=False,  # Don't fail on error
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            except Exception:
                pass  # Silent fail for performance

    def is_admin(self) -> bool:
        """Check if running with administrator privileges.
        Uses multiple methods to ensure accurate detection.
        """
        if platform.system() != "Windows":
            return False
        
        try:
            import ctypes
            
            # Method 1: Check using shell32.IsUserAnAdmin()
            try:
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
                if is_admin:
                    return True
            except:
                pass
            
            # Method 2: Try to write to a protected location (hosts file directory)
            try:
                test_file = self.hosts_path.parent / "test_write_access.tmp"
                test_file.write_text("test")
                test_file.unlink()
                return True
            except (PermissionError, IOError, OSError):
                return False
                
        except Exception:
            return False

    def backup_hosts(self, force: bool = False) -> bool:
        """Create a backup of the hosts file with automatic cleanup of old backups.
        
        Args:
            force: If True, always create backup. If False, only backup if file size changed
                  or significant time has passed since last backup (reduces unnecessary backups).
        """
        if not self.hosts_path.exists():
            return False

        try:
            current_size = self.hosts_path.stat().st_size
            current_time = datetime.now()
            
            # Skip backup if not forced and:
            # 1. File size hasn't changed
            # 2. Last backup was less than 1 hour ago (optimized to reduce disk usage)
            if not force and self.last_backup_time and self.last_backup_size:
                time_diff = (current_time - self.last_backup_time).total_seconds()
                if self.last_backup_size == current_size and time_diff < 3600:  # 1 hour
                    return True  # Skip backup - no significant change
            
            # Clean old backups first (keep only last 3 to save disk space)
            self._cleanup_old_backups(max_backups=3)
            
            timestamp = current_time.strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"hosts_backup_{timestamp}.txt"
            shutil.copy2(self.hosts_path, backup_file)
            
            # Update backup tracking
            self.last_backup_time = current_time
            self.last_backup_size = current_size
            
            return True
        except (IOError, PermissionError) as e:
            # Handle permission errors gracefully
            if isinstance(e, PermissionError):
                print(f"Warning: Could not create backup (permission denied). Continuing without backup.")
            elif isinstance(e, OSError) and hasattr(e, 'winerror') and e.winerror == 5:
                print(f"Warning: Could not create backup (access denied). Continuing without backup.")
            else:
                print(f"Error backing up hosts file: {e}")
            return False
    
    def _cleanup_old_backups(self, max_backups: int = 3) -> None:
        """Clean up old backup files, keeping only the most recent N backups.
        
        Args:
            max_backups: Maximum number of backup files to keep (default: 10)
        """
        try:
            if not self.backup_dir.exists():
                return
            
            # Get all backup files sorted by modification time (newest first)
            backup_files = sorted(
                self.backup_dir.glob("hosts_backup_*.txt"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            
            # Remove old backups if we exceed max_backups
            if len(backup_files) > max_backups:
                files_to_delete = backup_files[max_backups:]
                deleted_count = 0
                failed_count = 0
                for old_backup in files_to_delete:
                    try:
                        # Try to make file writable first (Windows)
                        try:
                            old_backup.chmod(0o666)  # Make writable
                        except:
                            pass  # Ignore chmod errors
                        
                        old_backup.unlink()
                        deleted_count += 1
                    except PermissionError:
                        # File is locked or access denied - skip silently
                        failed_count += 1
                        # Try to delete on next run, don't spam errors
                    except OSError as e:
                        # WinError 5 is Access Denied - skip silently
                        if e.winerror == 5:  # Access Denied
                            failed_count += 1
                        else:
                            # Other OS errors - log once
                            if failed_count == 0:  # Only log first error to avoid spam
                                print(f"Error removing old backup {old_backup.name}: {e}")
                            failed_count += 1
                    except Exception as e:
                        # Other errors - log once
                        if failed_count == 0:  # Only log first error to avoid spam
                            print(f"Error removing old backup {old_backup.name}: {e}")
                        failed_count += 1
                
                # Silent cleanup - no logging needed
                        
        except Exception:
            pass  # Silent fail

    def read_hosts(self) -> List[str]:
        """Read the hosts file and return lines."""
        if not self.hosts_path.exists():
            return []

        try:
            with open(self.hosts_path, "r", encoding="utf-8") as f:
                return f.readlines()
        except (IOError, PermissionError) as e:
            # Return empty list instead of raising - allows app to continue
            print(f"Warning: Cannot read hosts file: {e}")
            return []

    def get_blocked_domains(self) -> Set[str]:
        """Get set of currently blocked domains from hosts file."""
        try:
            lines = self.read_hosts()
            blocked = set()

            for line in lines:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                parts = line.split()
                if len(parts) >= 2 and parts[0] == self.redirect_ip:
                    # Extract domain (could be multiple domains on one line)
                    for part in parts[1:]:
                        if not part.startswith("#"):
                            blocked.add(part.lower())

            return blocked
        except Exception:
            return set()  # Return empty set if we can't read

    def block_domain(self, domain: str, force: bool = False) -> bool:
        """Block a domain by adding it to hosts file.
        
        Args:
            domain: Domain name to block
            force: If True, re-add domain even if it appears to be blocked (useful after unblocking)
        """
        domain = domain.lower().strip()
        if not domain:
            print(f"ERROR: Empty domain provided to block_domain")
            return False

        # Check if already blocked (skip if force=True)
        if not force:
            if domain in self.get_blocked_domains():
                print(f"Domain {domain} is already blocked")
                return True

        try:
            print(f"Attempting to block domain: {domain} (force={force})")
            # Backup before modification
            backup_success = self.backup_hosts()
            print(f"Backup {'succeeded' if backup_success else 'failed'}")

            # Read current hosts file
            lines = self.read_hosts()
            print(f"Read {len(lines)} lines from hosts file")

            # IMPORTANT: Always use ONE domain per line for reliability
            # Check if domain entry already exists and remove it first if force
            entry = f"{self.redirect_ip} {domain}\n"
            entry_found = False
            domain_in_file = False
            
            # First pass: find and remove existing entries if force
            # Also clean up any malformed entries (domains concatenated without spaces)
            if force:
                new_lines = []
                for line in lines:
                    line_stripped = line.strip()
                    if line_stripped.startswith(self.redirect_ip):
                        # Check for malformed entries (domains concatenated)
                        parts = line.split()
                        if len(parts) >= 2 and parts[0] == self.redirect_ip:
                            # Extract all domains from this line
                            domains_in_line = []
                            for part in parts[1:]:
                                if part.startswith("#"):
                                    break
                                # Check for concatenated domains (long domain names)
                                if len(part) > 50 or ('.' in part and part.count('.') > 4):
                                    # Likely malformed - skip this line
                                    print(f"Removing malformed entry: {line_stripped}")
                                    domain_in_file = True
                                    break
                                domains_in_line.append(part.lower())
                            else:
                                # Check if our domain is in this line
                                if domain in domains_in_line:
                                    domain_in_file = True
                                    # Remove domain from this line
                                    remaining_domains = [d for d in domains_in_line if d != domain]
                                    if remaining_domains:
                                        # Add each remaining domain on its own line for clarity
                                        for rem_domain in remaining_domains:
                                            new_lines.append(f"{self.redirect_ip} {rem_domain}\n")
                                    # Don't append original line (we've handled it)
                                    continue
                    new_lines.append(line)
                lines = new_lines
            else:
                # Normal pass: check if domain exists (checking for exact match)
                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    if line_stripped.startswith(self.redirect_ip):
                        parts = line.split()
                        if len(parts) >= 2 and parts[0] == self.redirect_ip:
                            # Check each part individually
                            for part in parts[1:]:
                                if part.startswith("#"):
                                    break
                                if part.lower() == domain:
                                    entry_found = True
                                    domain_in_file = True
                                    break
                            if entry_found:
                                break

            # Add entry if not found or if we forced removal
            # Always add ONE domain per line for maximum compatibility
            if not entry_found or force:
                # Add DeepFocus section comment if not present
                marker = "# DeepFocus entries"
                marker_found = any(marker in line for line in lines)
                
                if not marker_found:
                    lines.append(f"\n{marker}\n")
                # Add entry - ONE domain per line
                lines.append(entry)

            # Temporarily make file writable if read-only
            import stat
            was_readonly = False
            try:
                if not (self.hosts_path.stat().st_mode & stat.S_IWRITE):
                    was_readonly = True
                    self.hosts_path.chmod(stat.S_IREAD | stat.S_IWRITE)
            except:
                pass
            
            # Write back to hosts file
            with open(self.hosts_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            
            # Make read-only again if it was read-only
            if was_readonly:
                try:
                    self.hosts_path.chmod(stat.S_IREAD)
                except:
                    pass

            # Quick verification - check if domain is in file (don't re-read all domains)
            try:
                with open(self.hosts_path, "r", encoding="utf-8") as f:
                    content = f.read().lower()
                    if domain in content and f"{self.redirect_ip} {domain}" in content:
                        # Domain added successfully
                        return True
            except:
                pass

            # If quick check fails, do full verification
            blocked_domains = self.get_blocked_domains()
            return domain in blocked_domains

        except PermissionError:
            raise IOError("Cannot modify hosts file: Permission denied. Please run as administrator.")
        except IOError:
            raise
        except Exception as e:
            raise IOError(f"Cannot modify hosts file: {e}. Please run as administrator.")

    def unblock_domain(self, domain: str) -> bool:
        """Unblock a domain by removing it from hosts file."""
        domain = domain.lower().strip()
        if not domain:
            return False

        try:
            # Backup before modification
            self.backup_hosts()

            # Read current hosts file
            lines = self.read_hosts()
            modified = False
            new_lines = []

            for line in lines:
                # Skip lines containing this domain with redirect IP
                if line.strip().startswith(self.redirect_ip):
                    # Check if this line contains the domain
                    parts = line.split()
                    if len(parts) >= 2 and parts[0] == self.redirect_ip:
                        domains_in_line = [d.lower() for d in parts[1:] if not d.startswith("#")]
                        if domain in domains_in_line:
                            # Remove domain from this line
                            remaining_domains = [d for d in domains_in_line if d != domain]
                            if remaining_domains:
                                # Keep line with remaining domains
                                new_line = f"{self.redirect_ip} {' '.join(remaining_domains)}\n"
                                new_lines.append(new_line)
                            modified = True
                            continue

                new_lines.append(line)

            # Write back if modified
            if modified:
                # Temporarily make file writable if read-only
                import stat
                was_readonly = False
                try:
                    if not (self.hosts_path.stat().st_mode & stat.S_IWRITE):
                        was_readonly = True
                        self.hosts_path.chmod(stat.S_IREAD | stat.S_IWRITE)
                except:
                    pass
                
                with open(self.hosts_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                
                # Make read-only again if it was read-only
                if was_readonly:
                    try:
                        self.hosts_path.chmod(stat.S_IREAD)
                    except:
                        pass
                
                # Flush DNS cache
                self._flush_dns_cache()

            return modified

        except (IOError, PermissionError) as e:
            raise IOError(f"Cannot modify hosts file: {e}. Please run as administrator.")

    def block_domains(self, domains: List[str], force: bool = False) -> bool:
        """Block multiple domains efficiently - batch write for better performance.
        
        Args:
            domains: List of domain names to block
            force: If True, re-add domains even if they appear blocked (useful after unblocking)
        """
        if not domains:
            return True
        
        # Clean up malformed entries first if force=True
        if force:
            self._cleanup_malformed_entries()
        
        # Sanitize and prepare domains
        domains_to_block = []
        blocked_domains = self.get_blocked_domains() if not force else set()
        
        for domain in domains:
            domain = domain.strip().lower()
            if domain and domain not in blocked_domains:
                domains_to_block.append(domain)
        
        if not domains_to_block and not force:
            return True
        
        # Batch write all domains at once for performance
        try:
            # Backup before modification
            self.backup_hosts()
            
            # Read current hosts file
            lines = self.read_hosts()
            
            # Remove existing entries if force=True
            if force:
                new_lines = []
                blocked_set = set(domains_to_block)
                for line in lines:
                    line_stripped = line.strip()
                    if line_stripped.startswith(self.redirect_ip):
                        parts = line.split()
                        if len(parts) >= 2 and parts[0] == self.redirect_ip:
                            # Check for malformed or existing domains
                            domains_in_line = []
                            is_malformed = False
                            for part in parts[1:]:
                                if part.startswith("#"):
                                    break
                                part_lower = part.lower()
                                # Check for malformed entries
                                if len(part_lower) > 50 or part_lower.count('.') > 6:
                                    is_malformed = True
                                    break
                                if part_lower not in blocked_set:
                                    domains_in_line.append(part_lower)
                            
                            if is_malformed or any(d in blocked_set for d in domains_in_line):
                                # Skip this line - will be re-added properly
                                continue
                            elif domains_in_line:
                                # Keep remaining domains
                                new_lines.append(f"{self.redirect_ip} {' '.join(domains_in_line)}\n")
                                continue
                    new_lines.append(line)
                lines = new_lines
            
            # Add DeepFocus marker if not present
            marker = "# DeepFocus entries"
            marker_found = any(marker in line for line in lines)
            if not marker_found:
                lines.append(f"\n{marker}\n")
            
            # Add all domains at once (one per line for reliability)
            for domain in domains_to_block:
                lines.append(f"{self.redirect_ip} {domain}\n")
            
            # Write all at once - ensure we have admin privileges first
            import stat
            import ctypes
            
            # Verify admin privileges before attempting write
            try:
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
                if not is_admin:
                    raise PermissionError("Administrator privileges required to modify hosts file. Please run the application as Administrator.")
            except (AttributeError, OSError):
                # Not Windows or can't check - try anyway
                pass
            
            was_readonly = False
            try:
                # Check and remove read-only attribute if present
                file_stat = self.hosts_path.stat()
                if not (file_stat.st_mode & stat.S_IWRITE):
                    was_readonly = True
                    try:
                        # Remove read-only attribute
                        self.hosts_path.chmod(stat.S_IREAD | stat.S_IWRITE)
                    except (PermissionError, OSError) as chmod_err:
                        # If chmod fails, try using Windows API
                        try:
                            import win32api
                            import win32con
                            win32api.SetFileAttributes(str(self.hosts_path), win32con.FILE_ATTRIBUTE_NORMAL)
                        except (ImportError, OSError):
                            # If win32api not available or fails, raise the original error
                            raise PermissionError(
                                f"Unable to modify hosts file permissions. Error: {chmod_err}. "
                                "Please ensure the application is running as Administrator."
                            )
            except PermissionError:
                raise
            except Exception:
                # Non-critical permission error - continue silently
                pass
            
            # Attempt to write the file
            try:
                with open(self.hosts_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
            except PermissionError as e:
                # Provide helpful error message
                raise PermissionError(
                    f"Permission denied: Cannot write to hosts file. "
                    f"Please ensure:\n"
                    f"1. The application is running as Administrator\n"
                    f"2. No antivirus is blocking hosts file modifications\n"
                    f"3. The hosts file is not locked by another process\n"
                    f"Original error: {e}"
                )
            
            # Restore read-only attribute if it was set
            if was_readonly:
                try:
                    self.hosts_path.chmod(stat.S_IREAD)
                except (PermissionError, OSError):
                    # Non-critical - hosts file is readable
                    pass
            
            # Verify blocking (sample check - not all domains)
            # Flush DNS cache immediately after blocking for real-time effect
            self._flush_dns_cache()
            
            return True
            
        except Exception:
            return False
    
    def _cleanup_malformed_entries(self) -> None:
        """Clean up malformed domain entries in hosts file - ensure ONE domain per line."""
        try:
            lines = self.read_hosts()
            new_lines = []
            modified = False
            cleaned_domains = []
            
            for line in lines:
                line_stripped = line.strip()
                # Check for DeepFocus entries or any redirect entries
                if line_stripped.startswith(self.redirect_ip):
                    parts = line.split()
                    if len(parts) >= 2 and parts[0] == self.redirect_ip:
                        # Extract domain part (everything after IP, before #)
                        domain_part = ' '.join(parts[1:]).split('#')[0].strip()
                        
                        # Check for malformed entries:
                        # 1. Very long domain names (>50 chars)
                        # 2. Multiple www. patterns (indicates concatenation)
                        # 3. Multiple .com/.net/.org patterns
                        is_malformed = False
                        if len(domain_part) > 50:
                            is_malformed = True
                        elif domain_part.count('www.') > 1:
                            is_malformed = True
                        elif domain_part.count('.com') > 1 or domain_part.count('.net') > 1 or domain_part.count('.app') > 1:
                            is_malformed = True
                        elif domain_part.count('.') > 6:  # Too many dots indicates concatenation
                            is_malformed = True
                        
                        if is_malformed:
                            # Silent removal of malformed entries
                            modified = True
                            cleaned_domains.append(domain_part)
                            continue  # Skip this malformed entry
                        
                        # Valid entry - keep it as is
                        new_lines.append(line)
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            if modified:
                # Write cleaned hosts file
                import stat
                was_readonly = False
                try:
                    if not (self.hosts_path.stat().st_mode & stat.S_IWRITE):
                        was_readonly = True
                        self.hosts_path.chmod(stat.S_IREAD | stat.S_IWRITE)
                except:
                    pass
                
                with open(self.hosts_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                
                if was_readonly:
                    try:
                        self.hosts_path.chmod(stat.S_IREAD)
                    except:
                        pass
                
                print(f"Cleaned up {len(cleaned_domains)} malformed entries in hosts file")
                if cleaned_domains:
                    print(f"Removed malformed domains: {', '.join(cleaned_domains[:3])}...")
        except Exception as e:
            print(f"Error cleaning up malformed entries: {e}")
            import traceback
            traceback.print_exc()

    def unblock_domains(self, domains: List[str]) -> bool:
        """Unblock multiple domains."""
        success = True
        for domain in domains:
            if not self.unblock_domain(domain):
                success = False
        return success

    def restore_backup(self, backup_file: Path) -> bool:
        """Restore hosts file from a backup."""
        if not backup_file.exists():
            return False

        try:
            shutil.copy2(backup_file, self.hosts_path)
            return True
        except (IOError, PermissionError) as e:
            print(f"Error restoring backup: {e}")
            return False
