"""
System integration utilities: system tray, auto-start, admin checks.
Simplified and optimized.
"""
import sys
import platform
import winreg
from pathlib import Path
from typing import Optional, Callable
import threading


# Global tray icon singleton
_global_tray_icon = None
_global_tray_thread = None


class SystemIntegration:
    """Handles system-level integrations like tray icon and auto-start."""

    def __init__(self):
        self.is_windows = platform.system() == "Windows"

    def check_admin_privileges(self) -> bool:
        """Check if running with administrator privileges."""
        if not self.is_windows:
            return False
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def set_auto_start(self, enabled: bool, app_path: str) -> bool:
        """Set application to start automatically on Windows boot."""
        if not self.is_windows:
            return False

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )

            app_name = "DeepFocus"

            if enabled:
                if getattr(sys, 'frozen', False):
                    app_with_args = f'"{app_path}" --minimized'
                else:
                    app_with_args = f'"{app_path}" --minimized'
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_with_args)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass

            winreg.CloseKey(key)
            return True

        except Exception:
            return False

    def is_auto_start_enabled(self, app_name: str = "DeepFocus") -> bool:
        """Check if auto-start is enabled."""
        if not self.is_windows:
            return False

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )

            try:
                winreg.QueryValueEx(key, app_name)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False

        except Exception:
            return False

    def create_system_tray(
        self,
        icon_path: Optional[str],
        show_callback: Callable,
        quit_callback: Callable,
        menu_title: str = "DeepFocus"
    ):
        """Create system tray icon (singleton)."""
        return get_or_create_tray_icon(icon_path, show_callback, quit_callback, menu_title)

    def get_app_path(self) -> str:
        """Get the path to the current application executable."""
        if getattr(sys, 'frozen', False):
            return sys.executable
        else:
            return f'"{sys.executable}" -m src.main'


# Global instance
system_integration = SystemIntegration()


def stop_tray_icon():
    """Stop and reset the global tray icon. Call this on quit."""
    global _global_tray_icon, _global_tray_thread
    
    if _global_tray_icon is not None:
        try:
            _global_tray_icon.stop()
        except Exception:
            pass
        _global_tray_icon = None
    
    _global_tray_thread = None


def get_or_create_tray_icon(
    icon_path: Optional[str],
    show_callback: Callable,
    quit_callback: Callable,
    menu_title: str = "DeepFocus"
):
    """Get or create a single global system tray icon instance."""
    global _global_tray_icon, _global_tray_thread

    # If tray icon already exists and running, return it
    if _global_tray_icon is not None:
        try:
            if _global_tray_thread and _global_tray_thread.is_alive():
                return _global_tray_icon
        except Exception:
            pass

    try:
        import pystray
        from PIL import Image, ImageDraw

        # Create icon image
        if icon_path and Path(icon_path).exists():
            image = Image.open(icon_path)
        else:
            # Create default icon (blue with white square)
            image = Image.new('RGB', (64, 64), color='#1a5a4c')
            draw = ImageDraw.Draw(image)
            draw.rectangle([16, 16, 48, 48], fill='white')

        # Wrap quit callback to also stop tray icon
        def quit_with_cleanup():
            stop_tray_icon()
            quit_callback()

        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem("Show", lambda icon, item: show_callback()),
            pystray.MenuItem("Quit", lambda icon, item: quit_with_cleanup())
        )

        # Create tray icon
        _global_tray_icon = pystray.Icon(menu_title, image, menu_title, menu)

        # Run in separate daemon thread
        def run_tray():
            try:
                _global_tray_icon.run()
            except Exception:
                pass

        _global_tray_thread = threading.Thread(target=run_tray, daemon=True)
        _global_tray_thread.start()

        return _global_tray_icon

    except ImportError:
        return None
    except Exception:
        return None
