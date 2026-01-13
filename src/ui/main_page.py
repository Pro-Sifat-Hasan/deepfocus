"""
Main dashboard page with platform toggles and navigation.
"""
import flet as ft
from typing import Callable

from ..core.blocker import Blocker
from ..core.auth import auth
from ..config.constants import PLATFORM_DOMAINS, CASINO_GAMBLING_DOMAINS
from ..config.settings import settings
from ..config.colors import GREY_600, BLOCKED, UNBLOCKED, ERROR, SUCCESS, PRIMARY, WHITE, GREY_300, GREY_400
from ..utils.language import lang
from .components.platform_card import create_platform_card
from .components.footer import create_footer


class MainPage:
    """Main dashboard page manager."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.blocker = Blocker()
        self.platform_cards = {}
        self.content_column = None
        
        # CRITICAL: Apply blocking/unblocking based on settings (if admin)
        # This ensures persistence - both blocked AND unblocked states are respected
        if self.blocker.is_admin():
            print("Admin privileges detected - syncing blocking state with settings...")
            
            # Sync all platforms with their settings state
            # Respect both blocked (True) and unblocked (False) states
            for platform, domains in PLATFORM_DOMAINS.items():
                is_blocked_in_settings = settings.is_platform_blocked(platform)
                
                if is_blocked_in_settings:
                    try:
                        blocked_domains = self.blocker.hosts_manager.get_blocked_domains()
                        # Check if ALL domains are blocked (not just some)
                        all_blocked = all(domain in blocked_domains for domain in domains)
                        needs_blocking = not all_blocked
                        
                        if needs_blocking:
                            print(f"Applying blocking for {platform} (settings say blocked, hosts file doesn't match)...")
                            # Use blocker method which ensures proper persistence
                            success = self.blocker.block_platform(platform, force=True)
                            if success:
                                print(f"✓ Successfully blocked {platform} - state persisted")
                                # Verify persistence
                                settings.set_platform_blocked(platform, True)
                            else:
                                print(f"✗ Failed to block {platform} - settings still saved for retry")
                                # Still persist settings - will retry on next admin run
                                settings.set_platform_blocked(platform, True)
                        else:
                            # All domains are blocked - verify settings match
                            settings.set_platform_blocked(platform, True)
                            print(f"✓ {platform} is blocked (verified in hosts file)")
                    except Exception as e:
                        print(f"✗ Error blocking {platform}: {e}")
                        import traceback
                        traceback.print_exc()
                        # Ensure settings persist even on error
                        settings.set_platform_blocked(platform, True)
                else:
                    # Platform should be UNBLOCKED - ensure it stays unblocked
                    try:
                        blocked_domains = self.blocker.hosts_manager.get_blocked_domains()
                        # Check if any domains are blocked (should be none)
                        blocked_domains_for_platform = [d for d in domains if d in blocked_domains]
                        
                        if blocked_domains_for_platform:
                            print(f"Unblocking {platform} (settings say unblocked, but domains found in hosts file)...")
                            # Unblock all domains for this platform
                            success = self.blocker.unblock_platform(platform)
                            if success:
                                print(f"✓ Successfully unblocked {platform} - state persisted")
                                # Verify persistence
                                settings.set_platform_blocked(platform, False)
                            else:
                                print(f"✗ Failed to unblock {platform} - settings still saved for retry")
                                # Still persist settings - will retry on next admin run
                                settings.set_platform_blocked(platform, False)
                        else:
                            # All domains are unblocked - verify settings match
                            settings.set_platform_blocked(platform, False)
                            print(f"✓ {platform} is unblocked (verified in hosts file)")
                    except Exception as e:
                        print(f"✗ Error unblocking {platform}: {e}")
                        import traceback
                        traceback.print_exc()
                        # Ensure settings persist even on error
                        settings.set_platform_blocked(platform, False)
            
            # Block adult content if enabled - ALWAYS use blocker method for proper cleanup and verification
            if settings.is_adult_content_blocked():
                try:
                    from ..config.constants import ADULT_CONTENT_DOMAINS
                    print(f"Applying adult content blocking ({len(ADULT_CONTENT_DOMAINS)} domains)...")
                    # Use blocker method which includes cleanup, force mode, and verification
                    success = self.blocker.block_adult_content()
                    if success:
                        # Verify after blocking
                        blocked_domains = self.blocker.hosts_manager.get_blocked_domains()
                        blocked_count = sum(1 for domain in ADULT_CONTENT_DOMAINS if domain in blocked_domains)
                        print(f"✓ Adult content: {blocked_count}/{len(ADULT_CONTENT_DOMAINS)} domains verified in hosts file")
                    else:
                        print("✗ Failed to block adult content")
                except Exception as e:
                    print(f"✗ Error blocking adult content: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Block casino/gambling if enabled - ALWAYS use blocker method for proper cleanup and verification
            if settings.is_casino_gambling_blocked():
                try:
                    print(f"Applying casino/gambling blocking ({len(CASINO_GAMBLING_DOMAINS)} domains)...")
                    # Use blocker method which includes cleanup, force mode, and verification
                    success = self.blocker.block_casino_gambling()
                    if success:
                        # Verify after blocking
                        blocked_domains = self.blocker.hosts_manager.get_blocked_domains()
                        blocked_count = sum(1 for domain in CASINO_GAMBLING_DOMAINS if domain in blocked_domains)
                        print(f"✓ Casino/gambling: {blocked_count}/{len(CASINO_GAMBLING_DOMAINS)} domains verified in hosts file")
                    else:
                        print("✗ Failed to block casino/gambling")
                except Exception as e:
                    print(f"✗ Error blocking casino/gambling: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            print("INFO: Running without Administrator privileges.")
            print("Blocking features will not work, but you can use the app to manage settings.")
        
        # Sync settings with hosts file (only if admin)
        try:
            if self.blocker.is_admin():
                self.blocker.sync_with_hosts_file()
        except Exception as e:
            print(f"Error syncing with hosts file: {e}")

    def create_page(self) -> ft.Container:
        """Create the main page UI."""
        # Header
        header = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(lang.translate("main_title"), size=32, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Text(lang.translate("main_subtitle"), size=16, color=GREY_600, text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
            padding=ft.Padding.only(top=20, bottom=20),
        )

        # Create platform cards
        # Verify and sync blocking state before creating cards
        if self.blocker.is_admin():
            self.blocker.sync_with_hosts_file()
        
        cards = []
        for platform_key in PLATFORM_DOMAINS.keys():
            platform_name = lang.translate(platform_key)
            # Get state from settings (persistent source of truth)
            is_blocked = settings.is_platform_blocked(platform_key)
            has_password = auth.has_platform_password(platform_key)
            
            card = create_platform_card(
                platform=platform_key,
                platform_name=platform_name,
                is_blocked=is_blocked,
                has_password=has_password,
                on_toggle=self._handle_platform_toggle,
                page=self.page,
            )
            self.platform_cards[platform_key] = card
            cards.append(card)

        # Platforms section
        platforms_section = ft.Column(
            controls=[
                ft.Text(lang.translate("platforms"), size=20, weight=ft.FontWeight.BOLD),
                *cards,
            ],
            spacing=10,
        )
        
        platforms_container = ft.Container(
            content=platforms_section,
            padding=20,
        )

        # Adult content card
        is_blocked = settings.is_adult_content_blocked()
        adult_toggle = ft.Switch(
            value=is_blocked,
            label=lang.translate("adult_content"),
            active_color=BLOCKED,
            inactive_thumb_color=GREY_400,
            inactive_track_color=GREY_300,
            on_change=lambda e: self._handle_adult_content_toggle(e.control.value),
        )
        
        adult_content_card = ft.Card(
            content=ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(lang.translate("block_adult") if not is_blocked else lang.translate("unblock_adult"), size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(lang.translate("adult_content"), size=12, color=GREY_600),
                            ],
                            spacing=5,
                        ),
                        adult_toggle,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=15,
            ),
            elevation=2,
        )
        
        # Casino/Gambling content card
        casino_is_blocked = settings.is_casino_gambling_blocked()
        casino_toggle = ft.Switch(
            value=casino_is_blocked,
            label=lang.translate("casino_gambling"),
            active_color=BLOCKED,
            inactive_thumb_color=GREY_400,
            inactive_track_color=GREY_300,
            on_change=lambda e: self._handle_casino_gambling_toggle(e.control.value),
        )
        
        casino_gambling_card = ft.Card(
            content=ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(
                                    lang.translate("block_casino_gambling") if not casino_is_blocked else lang.translate("unblock_casino_gambling"),
                                    size=16,
                                    weight=ft.FontWeight.BOLD
                                ),
                                ft.Text(
                                    lang.translate("casino_gambling"),
                                    size=12,
                                    color=GREY_600
                                ),
                            ],
                            spacing=5,
                            expand=True,
                        ),
                        casino_toggle,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=15,
            ),
            elevation=2,
        )

        # Navigation buttons
        nav_buttons = ft.Row(
            controls=[
                ft.Button(lang.translate("custom_domains"), icon="language", on_click=lambda e: self._navigate_to_custom_domains(), bgcolor=PRIMARY, color=WHITE),
                ft.Button(lang.translate("settings"), icon="settings", on_click=lambda e: self._navigate_to_settings(), bgcolor=PRIMARY, color=WHITE),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )

        # Footer
        footer = create_footer()

        # Main content
        self.content_column = ft.Column(
            controls=[
                header,
                platforms_container,
                adult_content_card,
                casino_gambling_card,
                nav_buttons,
                footer,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
        )

        return ft.Container(
            content=self.content_column,
            padding=20,
            expand=True,
        )

    def _handle_platform_toggle(self, platform: str, new_state: bool) -> None:
        """Handle platform toggle."""
        if auth.has_platform_password(platform):
            self._show_password_dialog(
                platform,
                lambda password: self._toggle_platform_with_password(platform, new_state, password),
            )
            return
        self._toggle_platform(platform, new_state)

    def _toggle_platform_with_password(self, platform: str, new_state: bool, password: str) -> None:
        """Toggle platform after password verification."""
        if not auth.verify_platform_password(platform, password):
            self._show_error(lang.translate("incorrect_password"))
            self._reset_platform_toggle(platform)
            return
        self._toggle_platform(platform, new_state)

    def _toggle_platform(self, platform: str, new_state: bool) -> None:
        """Toggle platform block state."""
        # Update settings first (works without admin)
        was_blocked = settings.is_platform_blocked(platform)
        settings.set_platform_blocked(platform, new_state)
        
        # Try to apply blocking if admin, but don't fail if not
        if not self.blocker.is_admin():
            self._show_info(f"Settings updated. Run as Administrator to apply blocking.")
            self._update_platform_card(platform)
            return
        
        try:
            if new_state:
                # Block the platform - ALWAYS force re-blocking to ensure persistence
                # This ensures that if platform was unblocked, it gets properly blocked again
                force = True  # Always force to ensure proper blocking after unblock
                success = self.blocker.block_platform(platform, force=force)
                if success:
                    # Verify blocking was applied
                    blocked_domains = self.blocker.hosts_manager.get_blocked_domains()
                    platform_domains = PLATFORM_DOMAINS.get(platform, [])
                    is_actually_blocked = any(domain in blocked_domains for domain in platform_domains)
                    
                    if is_actually_blocked:
                        self._show_success(f"{lang.translate(platform)} blocked successfully")
                        self._update_platform_card(platform)
                    else:
                        # Try force blocking
                        success = self.blocker.block_platform(platform, force=True)
                        if success:
                            self._show_success(f"{lang.translate(platform)} blocked successfully")
                        else:
                            self._show_info(f"Settings saved. Blocking will apply when running as Administrator.")
                        self._update_platform_card(platform)
                else:
                    # Try force blocking
                    success = self.blocker.block_platform(platform, force=True)
                    if success:
                        self._show_success(f"{lang.translate(platform)} blocked successfully")
                    else:
                        self._show_info(f"Settings saved. Blocking will apply when running as Administrator.")
                    self._update_platform_card(platform)
            else:
                # Unblock the platform
                success = self.blocker.unblock_platform(platform)
                if success:
                    self._show_success(f"{lang.translate(platform)} unblocked successfully")
                    self._update_platform_card(platform)
                else:
                    self._show_info(f"Settings saved. Changes will apply when running as Administrator.")
                    self._update_platform_card(platform)
        except Exception as e:
            self._show_info(f"Settings saved. Error applying blocking: {str(e)}")
            self._update_platform_card(platform)

    def _handle_adult_content_toggle(self, new_state: bool) -> None:
        """Handle adult content toggle."""
        # Update settings first (works without admin)
        settings.set_adult_content_blocked(new_state)
        
        # Try to apply blocking if admin, but don't fail if not
        if not self.blocker.is_admin():
            self._show_info("Settings updated. Run as Administrator to apply blocking.")
            return
        
        try:
            if new_state:
                success = self.blocker.block_adult_content()
                if success:
                    from ..config.constants import ADULT_CONTENT_DOMAINS
                    self._show_success(f"Adult content blocked successfully ({len(ADULT_CONTENT_DOMAINS)} domains)")
                else:
                    self._show_info("Settings saved. Blocking will apply when running as Administrator.")
            else:
                success = self.blocker.unblock_adult_content()
                if success:
                    self._show_success("Adult content unblocked successfully")
                else:
                    self._show_info("Settings saved. Changes will apply when running as Administrator.")
        except Exception as e:
            self._show_info(f"Settings saved. Error applying blocking: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _handle_casino_gambling_toggle(self, new_state: bool) -> None:
        """Handle casino/gambling toggle."""
        # Update settings first (works without admin)
        settings.set_casino_gambling_blocked(new_state)
        
        # Try to apply blocking if admin, but don't fail if not
        if not self.blocker.is_admin():
            self._show_info("Settings updated. Run as Administrator to apply blocking.")
            return
        
        try:
            if new_state:
                success = self.blocker.block_casino_gambling()
                if success:
                    self._show_success(f"Casino/Gambling sites blocked successfully ({len(CASINO_GAMBLING_DOMAINS)} domains)")
                else:
                    self._show_info("Settings saved. Blocking will apply when running as Administrator.")
            else:
                success = self.blocker.unblock_casino_gambling()
                if success:
                    self._show_success("Casino/Gambling sites unblocked successfully")
                else:
                    self._show_info("Settings saved. Changes will apply when running as Administrator.")
        except Exception as e:
            self._show_info(f"Settings saved. Error applying blocking: {str(e)}")
            import traceback
            traceback.print_exc()

    def _reset_platform_toggle(self, platform: str) -> None:
        """Reset platform toggle to current state."""
        self._update_platform_card(platform)

    def _update_platform_card(self, platform: str) -> None:
        """Update platform card to reflect current state."""
        # Get state from settings (persistent source of truth)
        is_blocked_in_settings = settings.is_platform_blocked(platform)
        
        # Verify against hosts file if admin (for accuracy)
        if self.blocker.is_admin():
            is_blocked_in_hosts = self.blocker.is_platform_blocked(platform)
            # If settings and hosts don't match, sync them (settings is source of truth)
            if is_blocked_in_settings != is_blocked_in_hosts:
                print(f"Warning: {platform} state mismatch - syncing...")
                # Apply settings to hosts file to sync
                if is_blocked_in_settings:
                    self.blocker.block_platform(platform, force=True)
                else:
                    self.blocker.unblock_platform(platform)
        
        # Use settings as source of truth for UI
        platform_name = lang.translate(platform)
        is_blocked = settings.is_platform_blocked(platform)
        has_password = auth.has_platform_password(platform)
        
        new_card = create_platform_card(
            platform=platform,
            platform_name=platform_name,
            is_blocked=is_blocked,
            has_password=has_password,
            on_toggle=self._handle_platform_toggle,
            page=self.page,
        )
        
        self.platform_cards[platform] = new_card
        
        # Rebuild page to show updated card
        if self.content_column:
            for i, control in enumerate(self.content_column.controls):
                if isinstance(control, ft.Container) and hasattr(control.content, 'controls'):
                    for j, sub_control in enumerate(control.content.controls):
                        if isinstance(sub_control, ft.Card):
                            old_card = self.platform_cards.get(platform)
                            if old_card and sub_control == old_card:
                                control.content.controls[j] = new_card
                                self.page.update()
                                return

    def _show_password_dialog(self, platform: str, on_confirm: Callable[[str], None]) -> None:
        """Show password input dialog."""
        platform_name = lang.translate(platform)
        password_field = ft.TextField(
            label=lang.translate("password"),
            password=True,
            can_reveal_password=True,
            autofocus=True,
        )
        
        def handle_submit(e=None):
            if password_field.value:
                self.page.close_dialog()
                on_confirm(password_field.value)
        
        password_field.on_submit = handle_submit
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(lang.translate("enter_password")),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(lang.translate("password_for_platform", platform=platform_name)),
                        password_field,
                    ],
                    tight=True,
                ),
                width=300,
                padding=10,
            ),
            actions=[
                ft.TextButton(content=ft.Text(lang.translate("cancel")), on_click=lambda e: self.page.close_dialog()),
                ft.Button(lang.translate("ok"), on_click=handle_submit, bgcolor=PRIMARY, color=WHITE),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _show_error(self, message: str) -> None:
        """Show error message."""
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=ERROR)
        self.page.snack_bar.open = True
        self.page.update()

    def _show_success(self, message: str) -> None:
        """Show success message."""
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=SUCCESS)
        self.page.snack_bar.open = True
        self.page.update()

    def _show_info(self, message: str) -> None:
        """Show info message."""
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=PRIMARY)
        self.page.snack_bar.open = True
        self.page.update()

    def _navigate_to_custom_domains(self) -> None:
        """Navigate to custom domains page."""
        if hasattr(self.page, 'on_navigate') and self.page.on_navigate:
            self.page.on_navigate("custom_domains")

    def _navigate_to_settings(self) -> None:
        """Navigate to settings page."""
        if hasattr(self.page, 'on_navigate') and self.page.on_navigate:
            self.page.on_navigate("settings")
