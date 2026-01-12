"""
Settings management for user preferences.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

from .constants import SETTINGS_FILE, DEFAULT_PASSWORD


class Settings:
    """Manages application settings and user preferences."""

    def __init__(self):
        self.settings_file = Path(SETTINGS_FILE)
        self._settings: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load settings from file or create default settings."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    self._settings = json.load(f)
                # Ensure platform_blocked exists and defaults to True
                if "platform_blocked" not in self._settings:
                    self._settings["platform_blocked"] = {platform: True for platform in [
                        "facebook", "instagram", "linkedin", "twitter", "youtube",
                        "tiktok", "reddit", "snapchat"
                    ]}
                    self.save()
                else:
                    # Reset any False to True for platforms
                    for platform in ["facebook", "instagram", "linkedin", "twitter", "youtube", "tiktok", "reddit", "snapchat"]:
                        if platform not in self._settings["platform_blocked"]:
                            self._settings["platform_blocked"][platform] = True
                    # Ensure adult content blocking ALWAYS defaults to True
                    if "adult_content_blocked" not in self._settings or not self._settings.get("adult_content_blocked", True):
                        self._settings["adult_content_blocked"] = True
                        self.save()
                    # Ensure casino/gambling blocking ALWAYS defaults to True
                    if "casino_gambling_blocked" not in self._settings or not self._settings.get("casino_gambling_blocked", True):
                        self._settings["casino_gambling_blocked"] = True
                        self.save()
                    elif self._settings.get("platform_blocked"):
                        self.save()
            except (json.JSONDecodeError, IOError):
                self._settings = self._default_settings()
                self.save()
        else:
            self._settings = self._default_settings()
            self.save()

    def save(self) -> None:
        """Save settings to file."""
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving settings: {e}")

    def _default_settings(self) -> Dict[str, Any]:
        """Return default settings dictionary."""
        return {
            "language": "en",
            "auto_start": True,  # Default: auto-start enabled
            "main_password_hash": None,  # Will be set by auth module
            "platform_passwords": {},  # {platform_name: hashed_password}
            "platform_blocked": {platform: True for platform in [
                "facebook", "instagram", "linkedin", "twitter", "youtube",
                "tiktok", "reddit", "snapchat"
            ]},  # Default: all platforms blocked
            "custom_domains": [],
            "adult_content_blocked": True,  # Default: blocked
            "casino_gambling_blocked": True,  # Default: blocked
            "custom_domains_blocked": [],
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        self._settings[key] = value
        self.save()

    def get_language(self) -> str:
        """Get current language setting."""
        return self.get("language", "en")

    def set_language(self, language: str) -> None:
        """Set language preference."""
        self.set("language", language)

    def is_auto_start(self) -> bool:
        """Check if auto-start is enabled."""
        return self.get("auto_start", False)

    def set_auto_start(self, enabled: bool) -> None:
        """Set auto-start preference."""
        self.set("auto_start", enabled)

    def get_platform_password_hash(self, platform: str) -> Optional[str]:
        """Get password hash for a platform."""
        passwords = self.get("platform_passwords", {})
        return passwords.get(platform)

    def set_platform_password_hash(self, platform: str, password_hash: Optional[str]) -> None:
        """Set password hash for a platform."""
        passwords = self.get("platform_passwords", {})
        if password_hash:
            passwords[platform] = password_hash
        else:
            passwords.pop(platform, None)
        self.set("platform_passwords", passwords)

    def is_platform_blocked(self, platform: str) -> bool:
        """Check if a platform is currently blocked."""
        blocked = self.get("platform_blocked", {})
        # Default to True (blocked) if not set
        return blocked.get(platform, True)

    def set_platform_blocked(self, platform: str, blocked: bool) -> None:
        """Set blocked state for a platform."""
        blocked_state = self.get("platform_blocked", {})
        blocked_state[platform] = blocked
        self.set("platform_blocked", blocked_state)

    def get_custom_domains(self) -> list:
        """Get list of custom domains."""
        return self.get("custom_domains", [])

    def add_custom_domain(self, domain: str) -> None:
        """Add a custom domain."""
        domains = self.get("custom_domains", [])
        if domain not in domains:
            domains.append(domain)
            self.set("custom_domains", domains)

    def remove_custom_domain(self, domain: str) -> None:
        """Remove a custom domain."""
        domains = self.get("custom_domains", [])
        if domain in domains:
            domains.remove(domain)
            self.set("custom_domains", domains)

    def is_adult_content_blocked(self) -> bool:
        """Check if adult content blocking is enabled."""
        return self.get("adult_content_blocked", False)

    def set_adult_content_blocked(self, blocked: bool) -> None:
        """Set adult content blocking state."""
        self.set("adult_content_blocked", blocked)
    
    def is_casino_gambling_blocked(self) -> bool:
        """Check if casino/gambling blocking is enabled."""
        return self.get("casino_gambling_blocked", True)
    
    def set_casino_gambling_blocked(self, blocked: bool) -> None:
        """Set casino/gambling blocking state."""
        self.set("casino_gambling_blocked", blocked)

    def get_main_password_hash(self) -> Optional[str]:
        """Get main password hash."""
        return self.get("main_password_hash")

    def set_main_password_hash(self, password_hash: str) -> None:
        """Set main password hash."""
        self.set("main_password_hash", password_hash)


# Global settings instance
settings = Settings()
