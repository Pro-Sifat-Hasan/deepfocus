"""
Login page with password authentication.
"""
import flet as ft
from typing import Callable

from ..core.auth import auth
from ..utils.language import lang
from ..config.colors import ERROR, TRANSPARENT, PRIMARY, WHITE


def create_login_page(page: ft.Page, on_login_success: Callable) -> ft.Container:
    """
    Create login page.
    
    Args:
        page: Flet page instance
        on_login_success: Callback function to call on successful login
    
    Returns:
        Container widget with login UI
    """
    # Initialize main password if needed
    auth.initialize_main_password()
    
    # Error message
    error_text = ft.Text(
        "",
        color=ERROR,
        visible=False,
        size=12,
    )
    
    # Password field
    password_field = ft.TextField(
        label=lang.translate("login_password"),
        password=True,
        can_reveal_password=True,
        autofocus=True,
        on_submit=lambda e: _handle_login(page, password_field, error_text, on_login_success),
    )
    
    # Login button
    login_button = ft.Button(
        lang.translate("login_button"),
        on_click=lambda e: _handle_login(page, password_field, error_text, on_login_success),
        width=200,
        bgcolor=PRIMARY,
        color=WHITE,
    )
    
    # Login form
    login_form = ft.Column(
        controls=[
            ft.Text(
                lang.translate("login_title"),
                size=24,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Divider(height=20, color=TRANSPARENT),
            password_field,
            error_text,
            ft.Divider(height=10, color=TRANSPARENT),
            login_button,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
    )
    
    # Main container
    container = ft.Container(
        content=login_form,
        alignment=ft.Alignment.CENTER,
        padding=40,
        expand=True,
    )
    
    return container


def _handle_login(
    page: ft.Page,
    password_field: ft.TextField,
    error_text: ft.Text,
    on_login_success: Callable,
) -> None:
    """Handle login attempt."""
    password = password_field.value
    
    if not password:
        error_text.value = lang.translate("login_required")
        error_text.visible = True
        page.update()
        return
    
    # Verify password
    if auth.verify_main_password(password):
        error_text.visible = False
        password_field.value = ""
        page.update()
        on_login_success()
    else:
        error_text.value = lang.translate("login_error")
        error_text.visible = True
        password_field.value = ""
        page.update()
