"""
Language translation system for English and Bengali.
"""
from typing import Dict
from ..config.settings import settings


class LanguageManager:
    """Manages language translations and current language state."""

    def __init__(self):
        self.translations: Dict[str, Dict[str, str]] = {
            "en": self._get_english_translations(),
            "bn": self._get_bengali_translations(),
        }
        self.current_language = settings.get_language()

    def _get_english_translations(self) -> Dict[str, str]:
        """Get English translations."""
        return {
            # Login page
            "login_title": "DeepFocus Login",
            "login_password": "Password",
            "login_button": "Login",
            "login_error": "Incorrect password. Please try again.",
            "login_required": "Password required",
            
            # Main page
            "main_title": "DeepFocus",
            "main_subtitle": "Social Media Blocker",
            "platforms": "Platforms",
            "block": "Block",
            "unblock": "Unblock",
            "blocked": "Blocked",
            "unblocked": "Unblocked",
            "custom_domains": "Custom Domains",
            "settings": "Settings",
            "adult_content": "Adult Content",
            "block_adult": "Block Adult Content",
            "unblock_adult": "Unblock Adult Content",
            "casino_gambling": "Casino/Gambling",
            "block_casino_gambling": "Block Casino/Gambling",
            "unblock_casino_gambling": "Unblock Casino/Gambling",
            
            # Platform names
            "facebook": "Facebook",
            "instagram": "Instagram",
            "linkedin": "LinkedIn",
            "twitter": "Twitter/X",
            "youtube": "YouTube",
            "tiktok": "TikTok",
            "reddit": "Reddit",
            "snapchat": "Snapchat",
            
            # Custom domain page
            "add_domain": "Add Domain",
            "domain_input": "Enter domain (e.g., example.com)",
            "add_button": "Add",
            "remove_button": "Remove",
            "no_custom_domains": "No custom domains added",
            "domain_list": "Custom Domains List",
            "invalid_domain": "Invalid domain format",
            "domain_already_exists": "Domain already exists",
            "domain_added": "Domain added successfully",
            "domain_removed": "Domain removed successfully",
            
            # Settings page
            "settings_title": "Settings",
            "language": "Language",
            "language_english": "English",
            "language_bengali": "Bengali",
            "auto_start": "Start on Windows Boot",
            "auto_start_enabled": "Application will start automatically on boot",
            "auto_start_disabled": "Application will not start on boot",
            "change_main_password": "Change Main Password",
            "current_password": "Current Password",
            "new_password": "New Password",
            "confirm_password": "Confirm Password",
            "set_platform_password": "Set Password for Platform",
            "platform": "Platform",
            "password": "Password",
            "set_password": "Set Password",
            "remove_password": "Remove Password",
            "password_changed": "Password changed successfully",
            "passwords_not_match": "Passwords do not match",
            "incorrect_current_password": "Incorrect current password",
            "password_set": "Password set successfully",
            "password_removed": "Password removed successfully",
            "no_password": "No password set",
            "change_password": "Change Password",
            "settings_saved": "Settings saved successfully",
            
            # Common
            "save": "Save",
            "cancel": "Cancel",
            "close": "Close",
            "back": "Back",
            "yes": "Yes",
            "no": "No",
            "ok": "OK",
            "error": "Error",
            "success": "Success",
            "warning": "Warning",
            "info": "Information",
            "confirm": "Confirm",
            "delete": "Delete",
            "admin_required": "Administrator privileges required",
            "admin_required_msg": "This application requires administrator privileges to modify the hosts file.",
            "please_run_as_admin": "Please run this application as administrator.",
            
            # Password dialog
            "enter_password": "Enter Password",
            "password_for_platform": "Enter password for {platform}",
            "password_required": "Password required to {action}",
            "incorrect_password": "Incorrect password",
            
            # Footer
            "created_by": "Created by Sifat",
            
            # Status messages
            "blocking": "Blocking...",
            "unblocking": "Unblocking...",
            "blocked_success": "Successfully blocked",
            "unblocked_success": "Successfully unblocked",
            "block_failed": "Failed to block",
            "unblock_failed": "Failed to unblock",
        }

    def _get_bengali_translations(self) -> Dict[str, str]:
        """Get Bengali translations."""
        return {
            # Login page
            "login_title": "DeepFocus লগইন",
            "login_password": "পাসওয়ার্ড",
            "login_button": "লগইন",
            "login_error": "ভুল পাসওয়ার্ড। আবার চেষ্টা করুন।",
            "login_required": "পাসওয়ার্ড প্রয়োজন",
            
            # Main page
            "main_title": "DeepFocus",
            "main_subtitle": "সোশ্যাল মিডিয়া ব্লকার",
            "platforms": "প্ল্যাটফর্মসমূহ",
            "block": "ব্লক",
            "unblock": "আনব্লক",
            "blocked": "ব্লক করা হয়েছে",
            "unblocked": "আনব্লক করা হয়েছে",
            "custom_domains": "কাস্টম ডোমেইন",
            "settings": "সেটিংস",
            "adult_content": "প্রাপ্তবয়স্ক কনটেন্ট",
            "block_adult": "প্রাপ্তবয়স্ক কনটেন্ট ব্লক করুন",
            "unblock_adult": "প্রাপ্তবয়স্ক কনটেন্ট আনব্লক করুন",
            "casino_gambling": "ক্যাসিনো/জুয়া",
            "block_casino_gambling": "ক্যাসিনো/জুয়া ব্লক করুন",
            "unblock_casino_gambling": "ক্যাসিনো/জুয়া আনব্লক করুন",
            
            # Platform names
            "facebook": "Facebook",
            "instagram": "Instagram",
            "linkedin": "LinkedIn",
            "twitter": "Twitter/X",
            "youtube": "YouTube",
            "tiktok": "TikTok",
            "reddit": "Reddit",
            "snapchat": "Snapchat",
            
            # Custom domain page
            "add_domain": "ডোমেইন যোগ করুন",
            "domain_input": "ডোমেইন লিখুন (যেমন: example.com)",
            "add_button": "যোগ করুন",
            "remove_button": "মুছুন",
            "no_custom_domains": "কোন কাস্টম ডোমেইন নেই",
            "domain_list": "কাস্টম ডোমেইন তালিকা",
            "invalid_domain": "অবৈধ ডোমেইন ফরম্যাট",
            "domain_already_exists": "ডোমেইন ইতিমধ্যে আছে",
            "domain_added": "ডোমেইন সফলভাবে যোগ করা হয়েছে",
            "domain_removed": "ডোমেইন সফলভাবে মুছে ফেলা হয়েছে",
            
            # Settings page
            "settings_title": "সেটিংস",
            "language": "ভাষা",
            "language_english": "ইংরেজি",
            "language_bengali": "বাংলা",
            "auto_start": "Windows বুটে শুরু করুন",
            "auto_start_enabled": "অ্যাপ্লিকেশন স্বয়ংক্রিয়ভাবে বুটে শুরু হবে",
            "auto_start_disabled": "অ্যাপ্লিকেশন বুটে শুরু হবে না",
            "change_main_password": "মূল পাসওয়ার্ড পরিবর্তন করুন",
            "current_password": "বর্তমান পাসওয়ার্ড",
            "new_password": "নতুন পাসওয়ার্ড",
            "confirm_password": "পাসওয়ার্ড নিশ্চিত করুন",
            "set_platform_password": "প্ল্যাটফর্মের জন্য পাসওয়ার্ড সেট করুন",
            "platform": "প্ল্যাটফর্ম",
            "password": "পাসওয়ার্ড",
            "set_password": "পাসওয়ার্ড সেট করুন",
            "remove_password": "পাসওয়ার্ড মুছুন",
            "password_changed": "পাসওয়ার্ড সফলভাবে পরিবর্তন করা হয়েছে",
            "passwords_not_match": "পাসওয়ার্ড মেলে না",
            "incorrect_current_password": "বর্তমান পাসওয়ার্ড ভুল",
            "password_set": "পাসওয়ার্ড সফলভাবে সেট করা হয়েছে",
            "password_removed": "পাসওয়ার্ড সফলভাবে মুছে ফেলা হয়েছে",
            "no_password": "কোন পাসওয়ার্ড সেট নেই",
            "change_password": "পাসওয়ার্ড পরিবর্তন করুন",
            "settings_saved": "সেটিংস সফলভাবে সংরক্ষণ করা হয়েছে",
            
            # Common
            "save": "সংরক্ষণ",
            "cancel": "বাতিল",
            "close": "বন্ধ",
            "back": "পেছনে",
            "yes": "হ্যাঁ",
            "no": "না",
            "ok": "ঠিক আছে",
            "error": "ত্রুটি",
            "success": "সফল",
            "warning": "সতর্কতা",
            "info": "তথ্য",
            "confirm": "নিশ্চিত করুন",
            "delete": "মুছুন",
            "admin_required": "অ্যাডমিনিস্ট্রেটর সুবিধা প্রয়োজন",
            "admin_required_msg": "হোস্ট ফাইল পরিবর্তন করতে এই অ্যাপ্লিকেশনের জন্য অ্যাডমিনিস্ট্রেটর সুবিধা প্রয়োজন।",
            "please_run_as_admin": "অনুগ্রহ করে এই অ্যাপ্লিকেশনটি অ্যাডমিনিস্ট্রেটর হিসাবে চালান।",
            
            # Password dialog
            "enter_password": "পাসওয়ার্ড লিখুন",
            "password_for_platform": "{platform} এর জন্য পাসওয়ার্ড লিখুন",
            "password_required": "{action} করতে পাসওয়ার্ড প্রয়োজন",
            "incorrect_password": "ভুল পাসওয়ার্ড",
            
            # Footer
            "created_by": "Sifat দ্বারা তৈরি",
            
            # Status messages
            "blocking": "ব্লক করা হচ্ছে...",
            "unblocking": "আনব্লক করা হচ্ছে...",
            "blocked_success": "সফলভাবে ব্লক করা হয়েছে",
            "unblocked_success": "সফলভাবে আনব্লক করা হয়েছে",
            "block_failed": "ব্লক করতে ব্যর্থ",
            "unblock_failed": "আনব্লক করতে ব্যর্থ",
        }

    def get_current_language(self) -> str:
        """Get current language code."""
        return self.current_language

    def set_language(self, language: str) -> None:
        """Set current language."""
        if language in self.translations:
            self.current_language = language
            settings.set_language(language)

    def translate(self, key: str, **kwargs) -> str:
        """
        Get translated text for a key.
        
        Args:
            key: Translation key
            **kwargs: Format parameters for string formatting
        
        Returns:
            Translated text or key if not found
        """
        translations = self.translations.get(self.current_language, {})
        text = translations.get(key, key)
        
        # Format with kwargs if provided
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass
        
        return text

    def get(self, key: str, default: str = None, **kwargs) -> str:
        """Alias for translate method."""
        result = self.translate(key, **kwargs)
        if result == key and default:
            return default
        return result


# Global language manager instance
lang = LanguageManager()
