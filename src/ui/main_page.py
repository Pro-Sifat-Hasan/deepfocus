"""
Main dashboard page with platform toggles and navigation.
Simplified and optimized.
"""
import flet as ft
from typing import Callable

from ..core.blocker import Blocker
from ..core.auth import auth
from ..config.constants import PLATFORM_DOMAINS
from ..config.settings import settings
from ..config.colors import GREY_600, BLOCKED, ERROR, SUCCESS, PRIMARY, WHITE, GREY_300, GREY_400
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
        
        # Sync with hosts file on init (if admin)
        if self.blocker.is_admin():
            try:
                self.blocker.sync_with_hosts_file()
            except Exception:
                pass

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
        cards = []
        for platform_key in PLATFORM_DOMAINS.keys():
            platform_name = lang.translate(platform_key)
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
        adult_is_blocked = settings.is_adult_content_blocked()
        adult_toggle = ft.Switch(
            value=adult_is_blocked,
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
                                ft.Text(
                                    lang.translate("block_adult") if not adult_is_blocked else lang.translate("unblock_adult"),
                                    size=16,
                                    weight=ft.FontWeight.BOLD
                                ),
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
        
        # Casino/Gambling card
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
                                ft.Text(lang.translate("casino_gambling"), size=12, color=GREY_600),
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
                ft.ElevatedButton(
                    lang.translate("custom_domains"),
                    icon=ft.Icons.LANGUAGE,
                    on_click=lambda e: self._navigate_to_custom_domains(),
                    bgcolor=PRIMARY,
                    color=WHITE
                ),
                ft.ElevatedButton(
                    lang.translate("settings"),
                    icon=ft.Icons.SETTINGS,
                    on_click=lambda e: self._navigate_to_settings(),
                    bgcolor=PRIMARY,
                    color=WHITE
                ),
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
            self._update_platform_card(platform)
            return
        self._toggle_platform(platform, new_state)

    def _toggle_platform(self, platform: str, new_state: bool) -> None:
        """Toggle platform block state."""
        if not self.blocker.is_admin():
            self._show_error("Please run as Administrator to apply blocking")
            settings.set_platform_blocked(platform, new_state)
            self._update_platform_card(platform)
            return
        
        try:
            if new_state:
                success, error = self.blocker.block_platform(platform, force=True)
                if success:
                    self._show_success(f"{lang.translate(platform)} blocked successfully")
                else:
                    self._show_error(error or "Failed to block platform")
            else:
                success, error = self.blocker.unblock_platform(platform)
                if success:
                    self._show_success(f"{lang.translate(platform)} unblocked successfully")
                else:
                    self._show_error(error or "Failed to unblock platform")
            
            self._update_platform_card(platform)
            
        except Exception as e:
            self._show_error(f"Error: {str(e)}")
            self._update_platform_card(platform)

    def _handle_adult_content_toggle(self, new_state: bool) -> None:
        """Handle adult content toggle."""
        if not self.blocker.is_admin():
            self._show_error("Please run as Administrator to apply blocking")
            settings.set_adult_content_blocked(new_state)
            return
        
        try:
            if new_state:
                success, error = self.blocker.block_adult_content()
                if success:
                    self._show_success("Adult content blocked successfully")
                else:
                    self._show_error(error or "Failed to block adult content")
            else:
                success, error = self.blocker.unblock_adult_content()
                if success:
                    self._show_success("Adult content unblocked successfully")
                else:
                    self._show_error(error or "Failed to unblock adult content")
        except Exception as e:
            self._show_error(f"Error: {str(e)}")

    def _handle_casino_gambling_toggle(self, new_state: bool) -> None:
        """Handle casino/gambling toggle."""
        if not self.blocker.is_admin():
            self._show_error("Please run as Administrator to apply blocking")
            settings.set_casino_gambling_blocked(new_state)
            return
        
        try:
            if new_state:
                success, error = self.blocker.block_casino_gambling()
                if success:
                    self._show_success("Casino/Gambling sites blocked successfully")
                else:
                    self._show_error(error or "Failed to block casino/gambling sites")
            else:
                success, error = self.blocker.unblock_casino_gambling()
                if success:
                    self._show_success("Casino/Gambling sites unblocked successfully")
                else:
                    self._show_error(error or "Failed to unblock casino/gambling sites")
        except Exception as e:
            self._show_error(f"Error: {str(e)}")

    def _update_platform_card(self, platform: str) -> None:
        """Update platform card to reflect current state."""
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
        
        # Rebuild page
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
                self.page.close(dialog)
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
                ft.TextButton(content=ft.Text(lang.translate("cancel")), on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton(lang.translate("ok"), on_click=handle_submit, bgcolor=PRIMARY, color=WHITE),
            ],
        )
        
        self.page.open(dialog)

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

    def _navigate_to_custom_domains(self) -> None:
        """Navigate to custom domains page."""
        if hasattr(self.page, 'on_navigate') and self.page.on_navigate:
            self.page.on_navigate("custom_domains")

    def _navigate_to_settings(self) -> None:
        """Navigate to settings page."""
        if hasattr(self.page, 'on_navigate') and self.page.on_navigate:
            self.page.on_navigate("settings")
