"""
Reusable platform card component with toggle switch and password indicator.
"""
import flet as ft
from typing import Callable

from ...utils.language import lang
from ...config.colors import BLOCKED, UNBLOCKED, PRIMARY, TRANSPARENT, GREY_300, GREY_400


def create_platform_card(
    platform: str,
    platform_name: str,
    is_blocked: bool,
    has_password: bool,
    on_toggle: Callable[[str, bool], None],
    page: ft.Page,
) -> ft.Card:
    """Create a platform card with toggle switch."""
    status_text = lang.translate("blocked") if is_blocked else lang.translate("unblocked")
    
    toggle = ft.Switch(
        value=is_blocked,
        label=status_text,
        active_color=BLOCKED,
        inactive_thumb_color=GREY_400,
        inactive_track_color=GREY_300,
        on_change=lambda e: on_toggle(platform, e.control.value),
    )
    
    # Icon indicator (lock if password protected, otherwise transparent placeholder)
    leading_icon = ft.Icon(icon="lock", color=PRIMARY, size=20) if has_password else ft.Container(width=20)
    
    # Create card content with Row layout for better rendering
    card_content = ft.Container(
        content=ft.Row(
            controls=[
                leading_icon,
                ft.Text(
                    platform_name,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    expand=True,
                ),
                toggle,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=15,
    )
    
    return ft.Card(
        content=card_content,
        elevation=2,
    )
