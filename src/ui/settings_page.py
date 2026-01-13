"""
Settings page - Simplified.
"""
import flet as ft

from ..core.auth import auth
from ..config.constants import PLATFORM_DOMAINS
from ..config.settings import settings
from ..config.colors import GREY_600, ERROR, SUCCESS, PRIMARY, WHITE
from ..utils.language import lang
from ..utils.system_integration import system_integration
from .components.footer import create_footer


class SettingsPage:
    """Settings page manager."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.language_dropdown = None
        self.auto_start_switch = None

    def create_page(self) -> ft.Container:
        """Create the settings page UI."""
        # Header
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            tooltip="Back",
            on_click=lambda e: self._navigate_back(),
        )
        
        header = ft.Container(
            content=ft.Row(
                controls=[
                    back_button,
                    ft.Text(lang.translate("settings_title"), size=24, weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
            ),
            padding=ft.padding.only(top=20, bottom=20),
        )

        # Language selection
        self.language_dropdown = ft.Dropdown(
            label=lang.translate("language"),
            options=[
                ft.dropdown.Option("en", lang.translate("language_english")),
                ft.dropdown.Option("bn", lang.translate("language_bengali")),
            ],
            value=lang.get_current_language(),
            on_change=self._on_language_change,
            width=200,
        )

        language_section = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(lang.translate("language"), size=16, weight=ft.FontWeight.BOLD),
                        self.language_dropdown,
                    ],
                    spacing=10,
                ),
                padding=15,
            ),
            elevation=2,
        )

        # Auto-start setting
        auto_start_enabled = settings.is_auto_start()
        self.auto_start_switch = ft.Switch(
            label=lang.translate("auto_start"),
            value=auto_start_enabled,
            on_change=self._on_auto_start_change,
        )

        auto_start_section = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(lang.translate("auto_start"), size=16, weight=ft.FontWeight.BOLD),
                        self.auto_start_switch,
                        ft.Text(
                            lang.translate("auto_start_enabled") if auto_start_enabled else lang.translate("auto_start_disabled"),
                            size=12,
                            color=GREY_600,
                        ),
                    ],
                    spacing=10,
                ),
                padding=15,
            ),
            elevation=2,
        )

        # Change password section
        password_section = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(lang.translate("change_main_password"), size=16, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            lang.translate("change_main_password"),
                            icon=ft.Icons.LOCK,
                            on_click=self._show_change_password_dialog,
                            bgcolor=PRIMARY,
                            color=WHITE,
                        ),
                    ],
                    spacing=10,
                ),
                padding=15,
            ),
            elevation=2,
        )

        # Platform passwords section
        platform_passwords_section = self._create_platform_passwords_section()

        # Main content
        content = ft.Column(
            controls=[
                header,
                ft.Divider(),
                language_section,
                auto_start_section,
                password_section,
                platform_passwords_section,
                create_footer(),
            ],
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
        )

        return ft.Container(content=content, padding=20, expand=True)

    def _create_platform_passwords_section(self) -> ft.Card:
        """Create platform passwords management section."""
        password_cards = []
        
        for platform_key in PLATFORM_DOMAINS.keys():
            platform_name = lang.translate(platform_key)
            has_password = auth.has_platform_password(platform_key)
            
            row_controls = [
                ft.Column(
                    controls=[
                        ft.Text(platform_name, size=14, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            lang.translate("password_set") if has_password else lang.translate("no_password"),
                            size=12,
                            color=GREY_600,
                        ),
                    ],
                    spacing=5,
                    expand=True,
                ),
                ft.ElevatedButton(
                    lang.translate("set_password") if not has_password else lang.translate("change_password"),
                    icon=ft.Icons.LOCK if not has_password else ft.Icons.EDIT,
                    on_click=lambda e, p=platform_key: self._show_platform_password_dialog(p),
                    bgcolor=PRIMARY,
                    color=WHITE,
                ),
            ]
            
            if has_password:
                delete_button = ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=ERROR,
                    tooltip=lang.translate("remove_password"),
                    on_click=lambda e, p=platform_key: self._remove_platform_password(p),
                )
                row_controls.append(delete_button)
            
            password_card = ft.Card(
                content=ft.Container(
                    content=ft.Row(
                        controls=row_controls,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=10,
                ),
                elevation=1,
            )
            password_cards.append(password_card)

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(lang.translate("set_platform_password"), size=16, weight=ft.FontWeight.BOLD),
                        *password_cards,
                    ],
                    spacing=10,
                ),
                padding=15,
            ),
            elevation=2,
        )

    def _on_language_change(self, e: ft.ControlEvent) -> None:
        """Handle language change."""
        new_language = e.control.value
        lang.set_language(new_language)
        settings.set_language(new_language)
        
        if hasattr(self.page, 'on_navigate'):
            self.page.on_navigate("settings")

    def _on_auto_start_change(self, e: ft.ControlEvent) -> None:
        """Handle auto-start toggle."""
        enabled = e.control.value
        app_path = system_integration.get_app_path()
        
        success = system_integration.set_auto_start(enabled, app_path)
        
        if success:
            settings.set_auto_start(enabled)
            self._show_success(lang.translate("settings_saved"))
        else:
            self._show_error("Failed to set auto-start")
            e.control.value = not enabled
            self.page.update()

    def _show_change_password_dialog(self, e: ft.ControlEvent) -> None:
        """Show dialog to change main password."""
        current_field = ft.TextField(label=lang.translate("current_password"), password=True, can_reveal_password=True, autofocus=True)
        new_field = ft.TextField(label=lang.translate("new_password"), password=True, can_reveal_password=True)
        confirm_field = ft.TextField(label=lang.translate("confirm_password"), password=True, can_reveal_password=True)
        
        def handle_submit(e=None):
            if not current_field.value or not new_field.value or not confirm_field.value:
                return
            if new_field.value != confirm_field.value:
                self._show_error(lang.translate("passwords_not_match"))
                return
            if auth.change_main_password(current_field.value, new_field.value):
                self.page.close(dialog)
                self._show_success(lang.translate("password_changed"))
            else:
                self._show_error(lang.translate("incorrect_current_password"))
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(lang.translate("change_main_password")),
            content=ft.Container(
                content=ft.Column(controls=[current_field, new_field, confirm_field], tight=True),
                width=300,
                padding=10,
            ),
            actions=[
                ft.TextButton(content=ft.Text(lang.translate("cancel")), on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton(lang.translate("save"), on_click=handle_submit, bgcolor=PRIMARY, color=WHITE),
            ],
        )
        
        self.page.open(dialog)

    def _show_platform_password_dialog(self, platform: str) -> None:
        """Show dialog to set platform password."""
        platform_name = lang.translate(platform)
        password_field = ft.TextField(label=lang.translate("password"), password=True, can_reveal_password=True, autofocus=True)
        
        def handle_submit(e=None):
            if not password_field.value:
                return
            if auth.set_platform_password(platform, password_field.value):
                self.page.close(dialog)
                self._show_success(lang.translate("password_set"))
                if hasattr(self.page, 'on_navigate'):
                    self.page.on_navigate("settings")
            else:
                self._show_error(lang.translate("error"))
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(lang.translate("set_platform_password")),
            content=ft.Container(
                content=ft.Column(controls=[ft.Text(f"{lang.translate('platform')}: {platform_name}"), password_field], tight=True),
                width=300,
                padding=10,
            ),
            actions=[
                ft.TextButton(content=ft.Text(lang.translate("cancel")), on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton(lang.translate("save"), on_click=handle_submit, bgcolor=PRIMARY, color=WHITE),
            ],
        )
        
        self.page.open(dialog)

    def _remove_platform_password(self, platform: str) -> None:
        """Remove platform password."""
        auth.remove_platform_password(platform)
        self._show_success(lang.translate("password_removed"))
        if hasattr(self.page, 'on_navigate'):
            self.page.on_navigate("settings")

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

    def _navigate_back(self) -> None:
        """Navigate back to main page."""
        if hasattr(self.page, 'on_navigate'):
            self.page.on_navigate("main")
