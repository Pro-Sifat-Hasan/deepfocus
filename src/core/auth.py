"""
Authentication system for main password and per-platform passwords.
"""
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os

from ..config.constants import DEFAULT_PASSWORD
from ..config.settings import settings


class Auth:
    """Handles authentication and password management."""

    def __init__(self):
        self.salt_length = 16

    def _hash_password(self, password: str, salt: bytes = None) -> str:
        """Hash a password using PBKDF2."""
        if salt is None:
            salt = os.urandom(self.salt_length)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode('utf-8'))
        
        # Combine salt and key for storage
        combined = salt + key
        return base64.b64encode(combined).decode('utf-8')

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against a hash."""
        try:
            combined = base64.b64decode(password_hash.encode('utf-8'))
            salt = combined[:self.salt_length]
            stored_key = combined[self.salt_length:]
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            
            try:
                key = kdf.derive(password.encode('utf-8'))
                return key == stored_key
            except Exception:
                return False
        except Exception:
            return False

    def initialize_main_password(self) -> None:
        """Initialize main password if not set."""
        if settings.get_main_password_hash() is None:
            password_hash = self._hash_password(DEFAULT_PASSWORD)
            settings.set_main_password_hash(password_hash)

    def verify_main_password(self, password: str) -> bool:
        """Verify main application password."""
        try:
            password_hash = settings.get_main_password_hash()
            
            if password_hash is None:
                # Initialize with default password
                self.initialize_main_password()
                # Re-read hash after initialization
                password_hash = settings.get_main_password_hash()
                if password_hash is None:
                    # Still None - fallback to direct comparison
                    return password == DEFAULT_PASSWORD
            
            # Verify password against hash
            result = self._verify_password(password, password_hash)
            
            # Debug logging (can be removed in production)
            if not result:
                # Try to re-initialize if verification fails (settings might be corrupted)
                try:
                    settings_file = settings.settings_file
                    if not settings_file.exists() or settings_file.stat().st_size == 0:
                        # Settings file missing or empty - reinitialize
                        self.initialize_main_password()
                        return password == DEFAULT_PASSWORD
                except:
                    pass
            
            return result
        except Exception as e:
            # Fallback: if all else fails, try direct comparison with default
            print(f"Error verifying password: {e}")
            return password == DEFAULT_PASSWORD

    def change_main_password(self, old_password: str, new_password: str) -> bool:
        """Change main password."""
        if not self.verify_main_password(old_password):
            return False
        
        new_hash = self._hash_password(new_password)
        settings.set_main_password_hash(new_hash)
        return True

    def set_platform_password(self, platform: str, password: str) -> bool:
        """Set password for a platform."""
        if not password:
            return False
        
        password_hash = self._hash_password(password)
        settings.set_platform_password_hash(platform, password_hash)
        return True

    def remove_platform_password(self, platform: str) -> None:
        """Remove password for a platform."""
        settings.set_platform_password_hash(platform, None)

    def verify_platform_password(self, platform: str, password: str) -> bool:
        """Verify password for a platform."""
        password_hash = settings.get_platform_password_hash(platform)
        
        if password_hash is None:
            # No password set for this platform
            return True
        
        return self._verify_password(password, password_hash)

    def has_platform_password(self, platform: str) -> bool:
        """Check if a platform has a password set."""
        return settings.get_platform_password_hash(platform) is not None


# Global auth instance
auth = Auth()
