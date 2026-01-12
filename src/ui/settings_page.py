"""
Settings page for language, passwords, and auto-start configuration.
"""
import flet as ft
from typing import Callable

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
        # Header with back button - same pattern as custom domain page
        try:
            back_button = ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color=None,  # Use default color
                tooltip="Back",
                on_click=lambda e: self._navigate_back(),
            )
        except Exception as e:
            # Fallback: try string icon
            try:
                back_button = ft.IconButton(
                    icon="arrow_back",
                    tooltip="Back",
                    on_click=lambda e: self._navigate_back(),
                )
            except Exception as e2:
                # Final fallback: use TextButton
                back_button = ft.TextButton(
                    content=ft.Text("← Back"),
                    tooltip="Back",
                    on_click=lambda e: self._navigate_back(),
                )
        
        header = ft.Container(
            content=ft.Row(
                controls=[
                    back_button,
                    ft.Text(
                        lang.translate("settings_title"),
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.Padding.only(top=20, bottom=20),
        )

        # Language selection
        self.language_dropdown = ft.Dropdown(
            label=lang.translate("language"),
            options=[
                ft.dropdown.Option("en", lang.translate("language_english")),
                ft.dropdown.Option("bn", lang.translate("language_bengali")),
            ],
            value=lang.get_current_language(),
            on_select=self._on_language_change,
            width=200,
        )

        language_section = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            lang.translate("language"),
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
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
                        ft.Text(
                            lang.translate("auto_start"),
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
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

        # Change main password section
        password_section = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            lang.translate("change_main_password"),
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Button(
                            lang.translate("change_main_password"),
                            icon="lock",
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

        return ft.Container(
            content=content,
            padding=20,
            expand=True,
        )

    def _create_platform_passwords_section(self) -> ft.Card:
        """Create platform passwords management section."""
        password_cards = []
        
        for platform_key in PLATFORM_DOMAINS.keys():
            platform_name = lang.translate(platform_key)
            has_password = auth.has_platform_password(platform_key)
            
            # Build controls list conditionally
            row_controls = [
                ft.Column(
                    controls=[
                        ft.Text(
                            platform_name,
                            size=14,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            lang.translate("password_set") if has_password else lang.translate("no_password"),
                            size=12,
                            color=GREY_600,
                        ),
                    ],
                    spacing=5,
                    expand=True,
                ),
                ft.Button(
                    lang.translate("set_password") if not has_password else lang.translate("change_password"),
                    icon="lock" if not has_password else "edit",
                    on_click=lambda e, p=platform_key: self._show_platform_password_dialog(p),
                    bgcolor=PRIMARY,
                    color=WHITE,
                ),
            ]
            
            # Add delete IconButton only if password exists - same pattern as custom domain page
            if has_password:
                try:
                    delete_button = ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=ERROR,
                        tooltip=lang.translate("remove_password"),
                        on_click=lambda e, p=platform_key: self._remove_platform_password(p),
                    )
                except Exception as e:
                    # Fallback: try string icon
                    try:
                        delete_button = ft.IconButton(
                            icon="delete",
                            icon_color=ERROR,
                            tooltip=lang.translate("remove_password"),
                            on_click=lambda e, p=platform_key: self._remove_platform_password(p),
                        )
                    except Exception as e2:
                        # Final fallback: use Icon
                        delete_button = ft.Icon(ft.Icons.DELETE, color=ERROR)
                
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
                        ft.Text(
                            lang.translate("set_platform_password"),
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
                        *password_cards,
                    ],
                    spacing=10,
                ),
                padding=15,
            ),
            elevation=2,
        )

    def _on_language_change(self, e: ft.ControlEvent) -> None:
        """Handle language change - refresh page immediately."""
        new_language = e.control.value
        lang.set_language(new_language)
        settings.set_language(new_language)
        
        # Immediately refresh the settings page to show new language
        if hasattr(self.page, 'on_navigate'):
            # Trigger navigation to refresh the page
            self.page.on_navigate("settings")
        else:
            # Fallback: rebuild the page manually
            self._rebuild_page()
    
    def _rebuild_page(self) -> None:
        """Rebuild the settings page with current language."""
        settings_container = self.create_page()
        self.page.controls.clear()
        self.page.add(settings_container)
        self.page.update()

    def _on_auto_start_change(self, e: ft.ControlEvent) -> None:
        """Handle auto-start toggle change."""
        enabled = e.control.value
        app_path = system_integration.get_app_path()
        
        success = system_integration.set_auto_start(enabled, app_path)
        
        if success:
            settings.set_auto_start(enabled)
            if enabled:
                self._show_success("Auto-start enabled! App will start with administrator privileges on Windows boot.")
            else:
                self._show_success(lang.translate("settings_saved"))
        else:
            self._show_error("Failed to set auto-start. Please try again.")
            # Reset switch
            e.control.value = not enabled
            self.page.update()

    def _show_change_password_dialog(self, e: ft.ControlEvent) -> None:
        """Show dialog to change main password."""
        current_password_field = ft.TextField(
            label=lang.translate("current_password"),
            password=True,
            can_reveal_password=True,
            autofocus=True,
        )
        
        new_password_field = ft.TextField(
            label=lang.translate("new_password"),
            password=True,
            can_reveal_password=True,
        )
        
        confirm_password_field = ft.TextField(
            label=lang.translate("confirm_password"),
            password=True,
            can_reveal_password=True,
        )
        
        def handle_submit(e=None):
            current = current_password_field.value
            new = new_password_field.value
            confirm = confirm_password_field.value
            
            if not current or not new or not confirm:
                return
            
            if new != confirm:
                self._show_error(lang.translate("passwords_not_match"))
                return
            
            if auth.change_main_password(current, new):
                self.page.close_dialog()
                self._show_success(lang.translate("password_changed"))
            else:
                self._show_error(lang.translate("incorrect_current_password"))
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(lang.translate("change_main_password")),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        current_password_field,
                        new_password_field,
                        confirm_password_field,
                    ],
                    tight=True,
                ),
                width=300,
                padding=10,
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text(lang.translate("cancel")),
                    on_click=lambda e: self.page.close_dialog(),
                ),
                ft.Button(
                    lang.translate("save"),
                    on_click=handle_submit,
                    bgcolor=PRIMARY,
                    color=WHITE,
                ),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _show_platform_password_dialog(self, platform: str) -> None:
        """Show dialog to set platform password."""
        platform_name = lang.translate(platform)
        password_field = ft.TextField(
            label=lang.translate("password"),
            password=True,
            can_reveal_password=True,
            autofocus=True,
        )
        
        def handle_submit(e=None):
            password = password_field.value
            if not password:
                return
            
            if auth.set_platform_password(platform, password):
                self.page.close_dialog()
                self._show_success(lang.translate("password_set"))
                # Refresh the page
                self._refresh_page()
            else:
                self._show_error(lang.translate("error"))
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(lang.translate("set_platform_password")),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(lang.translate("platform") + ": " + platform_name),
                        password_field,
                    ],
                    tight=True,
                ),
                width=300,
                padding=10,
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text(lang.translate("cancel")),
                    on_click=lambda e: self.page.close_dialog(),
                ),
                ft.Button(
                    lang.translate("save"),
                    on_click=handle_submit,
                    bgcolor=PRIMARY,
                    color=WHITE,
                ),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _remove_platform_password(self, platform: str) -> None:
        """Remove platform password."""
        auth.remove_platform_password(platform)
        self._show_success(lang.translate("password_removed"))
        self._refresh_page()

    def _refresh_page(self) -> None:
        """Refresh the settings page."""
        # Recreate the page content
        # This would ideally be handled by the main app's navigation system
        pass

    def _show_error(self, message: str) -> None:
        """Show error message."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ERROR,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _show_success(self, message: str) -> None:
        """Show success message."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=SUCCESS,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _navigate_back(self) -> None:
        """Navigate back to main page."""
        if hasattr(self.page, 'on_navigate'):
            self.page.on_navigate("main")
