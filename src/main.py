"""
DeepFocus - Main application entry point.
Simplified and optimized.
"""
import flet as ft
import sys
import os
import asyncio
import platform
from pathlib import Path

# Add current and parent directories to path for imports
_current_dir = Path(__file__).resolve().parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))
if str(_current_dir.parent) not in sys.path:
    sys.path.insert(0, str(_current_dir.parent))

# Import application modules
try:
    from .ui.login_page import create_login_page
    from .ui.main_page import MainPage
    from .ui.custom_domain_page import CustomDomainPage
    from .ui.settings_page import SettingsPage
    from .utils.language import lang
    from .utils.system_integration import system_integration, stop_tray_icon
    from .core.blocker import Blocker
    from .config.colors import PRIMARY, WARNING, ERROR
    from .config.settings import settings
except ImportError:
    # Fallback for direct execution
    from src.ui.login_page import create_login_page
    from src.ui.main_page import MainPage
    from src.ui.custom_domain_page import CustomDomainPage
    from src.ui.settings_page import SettingsPage
    from src.utils.language import lang
    from src.utils.system_integration import system_integration, stop_tray_icon
    from src.core.blocker import Blocker
    from src.config.colors import PRIMARY, WARNING, ERROR
    from src.config.settings import settings


class App:
    """Main application class."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "DeepFocus"
        
        # Window properties
        self.page.window.width = 800
        self.page.window.height = 700
        self.page.window.min_width = 600
        self.page.window.min_height = 500
        self.page.window.resizable = True
        self.page.window.prevent_close = True
        
        # Window close handler - minimize to tray
        def on_window_event(e):
            try:
                is_close = (
                    (hasattr(e, 'data') and e.data == "close") or
                    str(e).lower().find("close") != -1
                )
                if is_close:
                    self.page.window.visible = False
                    self.page.update()
            except Exception:
                pass
        
        self.page.window.on_event = on_window_event
        
        # Tray icon reference
        self.tray_icon = None
        
        # Theme
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        self.page.theme = ft.Theme(font_family="Segoe UI", color_scheme_seed=PRIMARY)
        
        # Page state
        self.current_page = None
        self.is_logged_in = False
        
        # Initialize language
        lang.set_language(lang.get_current_language())
        
        # Setup navigation
        self.page.on_navigate = self._handle_navigation
        
        # Show login page
        self._show_login_page()
        
        # Initialize after UI shows
        self._initialize_services()

    def _initialize_services(self) -> None:
        """Initialize background services."""
        try:
            blocker = Blocker()
            if not blocker.is_admin():
                self._show_admin_warning()
            else:
                # Start protection
                try:
                    from .core.protection_monitor import protection_monitor
                except ImportError:
                    from src.core.protection_monitor import protection_monitor
                protection_monitor.start()
                protection_monitor.protect_hosts_file()
                
                # Setup tray
                self._setup_tray()
        except Exception:
            pass
        
        # Enable auto-start
        try:
            app_path = system_integration.get_app_path()
            system_integration.set_auto_start(True, app_path)
            if not settings.is_auto_start():
                settings.set_auto_start(True)
        except Exception:
            pass

    def _setup_tray(self) -> None:
        """Setup system tray icon."""
        def show_window():
            try:
                self.page.window.visible = True
                self.page.window.minimized = False
                self.page.update()
            except Exception:
                pass

        def quit_app():
            try:
                stop_tray_icon()
                self.page.window.close()
            except Exception:
                pass
            os._exit(0)

        icon_path = _current_dir / "assets" / "icon.ico"
        
        try:
            self.tray_icon = system_integration.create_system_tray(
                icon_path=str(icon_path) if icon_path.exists() else None,
                show_callback=show_window,
                quit_callback=quit_app,
                menu_title="DeepFocus",
            )
        except Exception:
            pass

    def _show_login_page(self) -> None:
        """Show login page."""
        try:
            self.is_logged_in = False
            login_container = create_login_page(self.page, self._on_login_success)
            self.page.controls.clear()
            self.page.add(login_container)
            self.page.update()
        except Exception as e:
            self._show_error_page(f"Error loading login: {e}")

    def _on_login_success(self) -> None:
        """Handle successful login."""
        try:
            self.is_logged_in = True
            
            # Apply blocking after login
            try:
                blocker = Blocker()
                if blocker.is_admin():
                    blocker.sync_with_hosts_file()
            except Exception as e:
                self._show_snackbar(f"Error applying blocking: {e}", ERROR)
            
            self._show_main_page()
        except Exception as e:
            self._show_snackbar(f"Error after login: {e}", ERROR)

    def _show_main_page(self) -> None:
        """Show main dashboard page."""
        try:
            main_page = MainPage(self.page)
            self.current_page = "main"
            main_container = main_page.create_page()
            self.page.controls.clear()
            self.page.add(main_container)
            self.page.update()
        except Exception as e:
            self._show_snackbar(f"Error loading main page: {e}", ERROR)

    def _show_custom_domains_page(self) -> None:
        """Show custom domains page."""
        try:
            custom_page = CustomDomainPage(self.page)
            self.current_page = "custom_domains"
            custom_container = custom_page.create_page()
            self.page.controls.clear()
            self.page.add(custom_container)
            self.page.update()
        except Exception:
            pass

    def _show_settings_page(self) -> None:
        """Show settings page."""
        settings_page = SettingsPage(self.page)
        self.current_page = "settings"
        settings_container = settings_page.create_page()
        self.page.controls.clear()
        self.page.add(settings_container)
        self.page.update()

    def _handle_navigation(self, route: str) -> None:
        """Handle navigation between pages."""
        if route == "main":
            self._show_main_page()
        elif route == "custom_domains":
            self._show_custom_domains_page()
        elif route == "settings":
            self._show_settings_page()

    def _show_admin_warning(self) -> None:
        """Show warning about admin privileges."""
        self._show_snackbar(lang.translate("admin_required_msg"), WARNING)

    def _show_snackbar(self, message: str, color) -> None:
        """Show a snackbar message."""
        try:
            self.page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=color, duration=5000)
            self.page.snack_bar.open = True
            self.page.update()
        except Exception:
            pass

    def _show_error_page(self, message: str) -> None:
        """Show error page."""
        self.page.controls.clear()
        self.page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Application Error", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text(message, size=12),
                    ],
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True,
                padding=40,
            )
        )
        self.page.update()


async def main(page: ft.Page):
    """Main entry point for Flet app."""
    try:
        start_minimized = "--minimized" in sys.argv or os.getenv("DEEPFOCUS_MINIMIZED", "").lower() == "true"
        
        app = App(page)
        
        await asyncio.sleep(0.1)
        await page.window.center()
        
        page.window.visible = not start_minimized
        page.update()
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            page.controls.clear()
            page.add(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Application Error", size=24, weight=ft.FontWeight.BOLD),
                            ft.Text(str(e), size=12),
                        ],
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    alignment=ft.alignment.center,
                    expand=True,
                    padding=40,
                )
            )
            page.window.visible = True
            page.update()
        except:
            pass


def check_single_instance() -> bool:
    """Prevent multiple instances on Windows."""
    if platform.system() != "Windows":
        return True
    try:
        import win32event
        import win32api
        from winerror import ERROR_ALREADY_EXISTS
        
        mutex_name = "Global\\DeepFocus_SingleInstance_Mutex"
        mutex = win32event.CreateMutex(None, False, mutex_name)
        
        if win32api.GetLastError() == ERROR_ALREADY_EXISTS:
            os._exit(1)
        return True
    except ImportError:
        return True
    except Exception:
        return True


def request_admin_elevation() -> bool:
    """Request admin elevation on Windows (for frozen exe only)."""
    if platform.system() != "Windows":
        return True
    
    try:
        import ctypes
        if ctypes.windll.shell32.IsUserAnAdmin() != 0:
            return True
        
        # Only auto-restart if running as EXE
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
            args = sys.argv[1:] if len(sys.argv) > 1 else []
            args_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in args)
            
            result = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe_path, args_str, None, 1)
            
            if result > 32:
                sys.exit(0)
        return False
    except Exception:
        return False


if __name__ == "__main__":
    # Prevent multiple instances
    check_single_instance()
    
    # Request admin on Windows
    if platform.system() == "Windows":
        request_admin_elevation()
    
    # Enable auto-start
    try:
        app_path = system_integration.get_app_path()
        system_integration.set_auto_start(True, app_path)
        settings.set_auto_start(True)
    except Exception:
        pass
    
    # Run app
    ft.run(main)
