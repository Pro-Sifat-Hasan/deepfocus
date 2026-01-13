"""
Custom domain management page - Simplified.
"""
import flet as ft

from ..core.blocker import Blocker
from ..utils.language import lang
from ..utils.validators import validate_domain, sanitize_domain
from ..config.colors import GREY_600, PRIMARY, ERROR, SUCCESS, WHITE
from .components.footer import create_footer


class CustomDomainPage:
    """Custom domain management page."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.blocker = Blocker()
        self.domain_list_view = None

    def create_page(self) -> ft.Container:
        """Create the custom domain page UI."""
        # Header with back button
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            tooltip="Back",
            on_click=lambda e: self._navigate_back(),
        )
        
        header = ft.Container(
            content=ft.Row(
                controls=[
                    back_button,
                    ft.Text(lang.translate("custom_domains"), size=24, weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
            ),
            padding=ft.padding.only(top=20, bottom=20),
        )

        # Domain input section
        domain_input = ft.TextField(
            label=lang.translate("domain_input"),
            hint_text="example.com",
            expand=True,
            on_submit=lambda e: self._add_domain(domain_input),
        )

        add_button = ft.ElevatedButton(
            lang.translate("add_button"),
            icon=ft.Icons.ADD,
            on_click=lambda e: self._add_domain(domain_input),
            bgcolor=PRIMARY,
            color=WHITE,
        )

        input_section = ft.Row(controls=[domain_input, add_button], spacing=10)

        # Domain list view
        self.domain_list_view = ft.Column(controls=[], spacing=0, scroll=ft.ScrollMode.AUTO)
        
        domain_list_container = ft.Card(
            content=ft.Container(
                content=self.domain_list_view,
                height=300,
                padding=ft.padding.symmetric(vertical=10),
            ),
        )

        # Main content
        content = ft.Column(
            controls=[
                header,
                ft.Divider(),
                input_section,
                ft.Divider(),
                ft.Text(lang.translate("domain_list"), size=18, weight=ft.FontWeight.BOLD),
                domain_list_container,
                create_footer(),
            ],
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
        )
        
        # Refresh domain list
        self._refresh_domain_list()
        
        return ft.Container(content=content, padding=20, expand=True)

    def _add_domain(self, domain_input: ft.TextField) -> None:
        """Add a custom domain."""
        domain = domain_input.value.strip()
        if not domain:
            return

        domain = sanitize_domain(domain)
        is_valid, error_msg = validate_domain(domain)
        
        if not is_valid:
            self._show_error(error_msg or lang.translate("invalid_domain"))
            return

        custom_domains = self.blocker.get_custom_domains()
        if domain in custom_domains:
            self._show_error(lang.translate("domain_already_exists"))
            return

        if not self.blocker.is_admin():
            self._show_error(lang.translate("admin_required_msg"))
            return

        success, error_msg = self.blocker.block_custom_domain(domain)
        
        if success:
            domain_input.value = ""
            self._refresh_domain_list()
            self._show_success(lang.translate("domain_added"))
            self.page.update()
        else:
            self._show_error(error_msg or lang.translate("error"))

    def _remove_domain(self, domain: str) -> None:
        """Remove a custom domain."""
        if not self.blocker.is_admin():
            self._show_error(lang.translate("admin_required_msg"))
            return

        success, error_msg = self.blocker.unblock_custom_domain(domain)
        
        if success:
            self._refresh_domain_list()
            self._show_success(lang.translate("domain_removed"))
            self.page.update()
        else:
            self._show_error(error_msg or lang.translate("error"))

    def _refresh_domain_list(self) -> None:
        """Refresh the domain list display."""
        if not self.domain_list_view:
            return

        self.domain_list_view.controls.clear()
        custom_domains = self.blocker.get_custom_domains()

        if not custom_domains:
            empty_tile = ft.ListTile(
                leading=ft.Icon(ft.Icons.LANGUAGE, color=GREY_600, opacity=0.5),
                title=ft.Text(lang.translate("no_custom_domains"), color=GREY_600),
            )
            self.domain_list_view.controls.append(empty_tile)
        else:
            for domain in custom_domains:
                delete_button = ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=ERROR,
                    tooltip=lang.translate("remove_button"),
                    on_click=lambda e, d=domain: self._remove_domain(d),
                )
                
                list_tile = ft.ListTile(
                    leading=ft.Icon(ft.Icons.LANGUAGE, color=PRIMARY),
                    title=ft.Text(domain),
                    trailing=delete_button,
                )
                self.domain_list_view.controls.append(list_tile)

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
        if hasattr(self.page, 'on_navigate') and self.page.on_navigate:
            self.page.on_navigate("main")
