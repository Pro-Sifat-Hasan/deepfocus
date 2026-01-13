"""
Footer component showing creator information.
"""
import flet as ft

from ...utils.language import lang
from ...config.colors import GREY_600


def create_footer() -> ft.Container:
    """Create footer component with creator information - always in English."""
    # Always show in English, regardless of language setting
    footer_text = "Created by Sifat"
    
    return ft.Container(
        content=ft.Text(
            footer_text,
            size=12,
            color=GREY_600,
            text_align=ft.TextAlign.CENTER,
        ),
        padding=ft.padding.only(bottom=10),
        alignment=ft.alignment.center,
    )
