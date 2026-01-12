"""
Custom domain management page.
"""
import flet as ft
from typing import List, Callable
import traceback

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
        print("[CustomDomainPage] Initialized")

    def create_page(self) -> ft.Container:
        """Create the custom domain page UI."""
        try:
            print("[CustomDomainPage] Starting create_page()...")
            
            # Header with back button - using ft.Icons constant (correct Flet API per documentation)
            try:
                print("[CustomDomainPage] Creating back button...")
                back_button = ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=None,  # Use default color
                    tooltip="Back",
                    on_click=lambda e: self._navigate_back(),
                )
                print("[CustomDomainPage] Back button created successfully")
            except Exception as e:
                print(f"[CustomDomainPage] Error creating back button with ft.Icons: {e}")
                traceback.print_exc()
                # Fallback: try string icon
                try:
                    back_button = ft.IconButton(
                        icon="arrow_back",
                        tooltip="Back",
                        on_click=lambda e: self._navigate_back(),
                    )
                    print("[CustomDomainPage] Back button created with string icon as fallback")
                except Exception as e2:
                    print(f"[CustomDomainPage] Error with string icon fallback: {e2}")
                    # Final fallback: use TextButton with content property
                    back_button = ft.TextButton(
                        content=ft.Text("← Back"),
                        on_click=lambda e: self._navigate_back(),
                        tooltip="Back",
                    )
        
            print("[CustomDomainPage] Creating header...")
            header = ft.Container(
                content=ft.Row(
                    controls=[
                        back_button,
                        ft.Text(
                            lang.translate("custom_domains"),
                            size=24,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                    spacing=10,
                ),
                padding=ft.padding.only(top=20, bottom=20),  # Padding.only per Flet docs
            )
            print("[CustomDomainPage] Header created successfully")

            # Domain input section
            print("[CustomDomainPage] Creating input section...")
            domain_input = ft.TextField(
                label=lang.translate("domain_input"),
                hint_text="example.com",
                expand=True,
                on_submit=lambda e: self._add_domain(domain_input),
            )

            add_button = ft.Button(
                lang.translate("add_button"),
                icon="add",
                on_click=lambda e: self._add_domain(domain_input),
                bgcolor=PRIMARY,
                color=WHITE,
            )

            input_section = ft.Row(
                controls=[domain_input, add_button],
                spacing=10,
            )
            print("[CustomDomainPage] Input section created successfully")

            # Domain list view - Column with ListTiles per Flet ListTile docs
            print("[CustomDomainPage] Creating domain list view...")
            self.domain_list_view = ft.Column(
                controls=[],
                spacing=0,  # No spacing between ListTiles per Flet ListTile docs example
                scroll=ft.ScrollMode.AUTO,  # Enable scrolling per Flet Column docs
            )
            print("[CustomDomainPage] Domain list view created successfully")
            
            # Domain list container - Card with Container per Flet ListTile docs example
            print("[CustomDomainPage] Creating domain list container...")
            domain_list_container = ft.Card(
                content=ft.Container(
                    content=self.domain_list_view,
                    height=300,  # Fixed height enables scrolling
                    padding=ft.padding.symmetric(vertical=10),  # Padding per Flet ListTile docs example
                ),
            )
            print("[CustomDomainPage] Domain list container created successfully")

            # Create footer
            print("[CustomDomainPage] Creating footer...")
            try:
                footer = create_footer()
                print("[CustomDomainPage] Footer created successfully")
            except Exception as e:
                print(f"[CustomDomainPage] Error creating footer: {e}")
                footer = ft.Text("Created by Sifat", size=12, color=GREY_600)

            # Main content Column per Flet Column documentation
            print("[CustomDomainPage] Assembling main content...")
            content = ft.Column(
                controls=[
                    header,
                    ft.Divider(),
                    input_section,
                    ft.Divider(),
                    ft.Text(
                        lang.translate("domain_list"),
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),
                    domain_list_container,
                    footer,
                ],
                spacing=15,  # Spacing per Flet docs
                scroll=ft.ScrollMode.AUTO,  # Enable scrolling per Flet docs
            )
            print("[CustomDomainPage] Main content assembled successfully")
            print(f"[CustomDomainPage] Content has {len(content.controls)} controls")
            
            # Update domain list AFTER creating the view
            print("[CustomDomainPage] Refreshing domain list...")
            try:
                self._refresh_domain_list()
                print("[CustomDomainPage] Domain list refreshed successfully")
            except Exception as e:
                print(f"[CustomDomainPage] Error refreshing domain list: {e}")
                traceback.print_exc()
            
            # Create main container per Flet Container documentation
            print("[CustomDomainPage] Creating main container...")
            main_container = ft.Container(
                content=content,
                padding=20,  # Padding as number per Flet docs
                expand=True,
            )
            print("[CustomDomainPage] Main container created successfully")
            
            print("[CustomDomainPage] create_page() completed successfully")
            return main_container
            
        except Exception as e:
            print(f"[CustomDomainPage] CRITICAL ERROR in create_page(): {e}")
            traceback.print_exc()
            # Return error container instead of crashing
            return self._create_error_container(str(e))

    def _add_domain(self, domain_input: ft.TextField) -> None:
        """Add a custom domain."""
        domain = domain_input.value.strip()
        
        if not domain:
            return

        # Sanitize domain
        domain = sanitize_domain(domain)

        # Validate domain
        is_valid, error_msg = validate_domain(domain)
        if not is_valid:
            self._show_error(error_msg or lang.translate("invalid_domain"))
            return

        # Check if already exists
        custom_domains = self.blocker.get_custom_domains()
        if domain in custom_domains:
            self._show_error(lang.translate("domain_already_exists"))
            return

        # Check admin privileges
        if not self.blocker.is_admin():
            self._show_error(lang.translate("admin_required_msg"))
            return

        # Block the domain
        success, error_msg = self.blocker.block_custom_domain(domain)
        
        if success:
            domain_input.value = ""
            self._refresh_domain_list()
            self._show_success(lang.translate("domain_added"))
        else:
            self._show_error(error_msg or lang.translate("error"))

    def _remove_domain(self, domain: str) -> None:
        """Remove a custom domain."""
        # Check admin privileges
        if not self.blocker.is_admin():
            self._show_error(lang.translate("admin_required_msg"))
            return

        # Unblock the domain
        success = self.blocker.unblock_custom_domain(domain)
        
        if success:
            self._refresh_domain_list()
            # Update the page to reflect the removal
            self.page.update()
            self._show_success(lang.translate("domain_removed"))
        else:
            self._show_error(lang.translate("error"))

    def _refresh_domain_list(self) -> None:
        """Refresh the domain list display."""
        try:
            print("[CustomDomainPage] _refresh_domain_list() called")
            if not self.domain_list_view:
                print("[CustomDomainPage] WARNING: domain_list_view is None")
                return

            # Clear existing controls
            self.domain_list_view.controls.clear()
            print("[CustomDomainPage] Cleared existing domain list controls")

            # Get custom domains
            try:
                custom_domains = self.blocker.get_custom_domains()
                print(f"[CustomDomainPage] Retrieved {len(custom_domains)} custom domains")
            except Exception as e:
                print(f"[CustomDomainPage] Error getting custom domains: {e}")
                custom_domains = []

            if not custom_domains:
                # Show empty state - simple ListTile per Flet docs
                print("[CustomDomainPage] Showing empty state")
                empty_tile = ft.ListTile(
                    leading=ft.Icon(ft.Icons.LANGUAGE, color=GREY_600, opacity=0.5),
                    title=ft.Text(
                        lang.translate("no_custom_domains"),
                        color=GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                )
                self.domain_list_view.controls.append(empty_tile)
                print("[CustomDomainPage] Empty state ListTile added")
            else:
                # Add domain list tiles - simple ListTile per Flet docs
                print("[CustomDomainPage] Creating domain list tiles...")
                for i, domain in enumerate(custom_domains):
                    try:
                        print(f"[CustomDomainPage] Creating list tile {i+1}/{len(custom_domains)} for domain: {domain}")
                        # Create delete IconButton - match back button style
                        try:
                            delete_button = ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color=ERROR,
                                tooltip=lang.translate("remove_button"),
                                on_click=lambda e, d=domain: self._remove_domain(d),
                            )
                            print(f"[CustomDomainPage] Delete IconButton created with ft.Icons.DELETE for {domain}")
                        except Exception as e:
                            print(f"[CustomDomainPage] Error creating IconButton with ft.Icons for {domain}: {e}")
                            traceback.print_exc()
                            # Fallback: try string icon
                            try:
                                delete_button = ft.IconButton(
                                    icon="delete",
                                    icon_color=ERROR,
                                    tooltip=lang.translate("remove_button"),
                                    on_click=lambda e, d=domain: self._remove_domain(d),
                                )
                                print(f"[CustomDomainPage] Delete IconButton created with string icon for {domain}")
                            except Exception as e2:
                                print(f"[CustomDomainPage] Error with string icon fallback for {domain}: {e2}")
                                # Final fallback: use Icon
                                delete_button = ft.Icon(ft.Icons.DELETE, color=ERROR)
                        
                        # Create ListTile per Flet ListTile documentation - simple and clean
                        list_tile = ft.ListTile(
                            leading=ft.Icon(ft.Icons.LANGUAGE, color=PRIMARY),
                            title=ft.Text(domain),
                            trailing=delete_button,
                        )
                        self.domain_list_view.controls.append(list_tile)
                        print(f"[CustomDomainPage] ListTile created and appended for {domain}")
                        print(f"[CustomDomainPage] Domain list view now has {len(self.domain_list_view.controls)} controls")
                    except Exception as e:
                        print(f"[CustomDomainPage] Error creating list tile for domain {domain}: {e}")
                        traceback.print_exc()
                        continue
                
                print(f"[CustomDomainPage] Successfully created {len(self.domain_list_view.controls)} domain list tiles")
            
            print("[CustomDomainPage] Domain list refresh completed")
            print(f"[CustomDomainPage] Final domain_list_view has {len(self.domain_list_view.controls)} controls")
                
        except Exception as e:
            print(f"[CustomDomainPage] CRITICAL ERROR in _refresh_domain_list(): {e}")
            traceback.print_exc()

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

    def _create_error_container(self, error_message: str) -> ft.Container:
        """Create an error container to display when page creation fails."""
        print(f"[CustomDomainPage] Creating error container with message: {error_message}")
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Error Loading Custom Domain Page",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ERROR,
                    ),
                    ft.Text(
                        f"Error: {error_message}",
                        size=14,
                        color=GREY_600,
                    ),
                    ft.Divider(),
                    ft.TextButton(
                        content=ft.Text("← Back to Main"),
                        on_click=lambda e: self._navigate_back(),
                    ),
                ],
                spacing=15,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=40,  # Simple number padding
            alignment=ft.alignment.center,  # Center alignment - use lowercase
            expand=True,
        )

    def _navigate_back(self) -> None:
        """Navigate back to main page."""
        print("[CustomDomainPage] Navigating back to main page")
        try:
            if hasattr(self.page, 'on_navigate') and self.page.on_navigate:
                self.page.on_navigate("main")
            else:
                print("[CustomDomainPage] WARNING: page.on_navigate not available")
        except Exception as e:
            print(f"[CustomDomainPage] Error navigating back: {e}")
            traceback.print_exc()
