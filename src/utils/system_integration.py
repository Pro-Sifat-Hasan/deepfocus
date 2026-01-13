"""
System integration utilities: system tray, auto-start, admin checks.
"""
import sys
import platform
import winreg
from pathlib import Path
from typing import Optional, Callable


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
        """
        Set application to start automatically on Windows boot with administrator privileges.
        
        Args:
            enabled: True to enable, False to disable
            app_path: Full path to the application executable
        
        Returns:
            True if successful, False otherwise
        """
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
                # Check if running as exe (frozen) or script
                if getattr(sys, 'frozen', False):
                    # For exe: launch with --minimized flag to start in tray
                    # The app will automatically request admin privileges on startup
                    # No need to use "runas" in registry - the EXE manifest handles it
                    app_with_args = f'"{app_path}" --minimized'
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_with_args)
                else:
                    # For script: direct path with minimized flag
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{app_path}" --minimized')
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass  # Already removed

            winreg.CloseKey(key)
            return True

        except Exception as e:
            print(f"Error setting auto-start: {e}")
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
        """
        Create system tray icon.
        
        Args:
            icon_path: Path to icon file (optional)
            show_callback: Function to call when showing window
            quit_callback: Function to call when quitting
            menu_title: Title for tray menu
        
        Returns:
            Tray icon instance or None
        """
        try:
            import pystray
            from PIL import Image, ImageDraw
            import threading
            
            # Use class variable to track if tray icon already exists
            if not hasattr(self, '_tray_icon') or self._tray_icon is None:
                # Create default icon if none provided
                if icon_path and Path(icon_path).exists():
                    image = Image.open(icon_path)
                else:
                    # Create a simple default icon (blue background with white square)
                    image = Image.new('RGB', (64, 64), color='blue')
                    draw = ImageDraw.Draw(image)
                    draw.rectangle([16, 16, 48, 48], fill='white')

                # Create menu
                menu = pystray.Menu(
                    pystray.MenuItem("Show", show_callback),
                    pystray.MenuItem("Quit", quit_callback)
                )

                # Create tray icon
                self._tray_icon = pystray.Icon(menu_title, image, menu_title, menu)

                # Run in separate thread (only if not already running)
                if not hasattr(self, '_tray_thread') or not self._tray_thread.is_alive():
                    def run_tray():
                        try:
                            self._tray_icon.run()
                        except Exception as e:
                            print(f"Tray icon error: {e}")

                    self._tray_thread = threading.Thread(target=run_tray, daemon=True)
                    self._tray_thread.start()
                    print("System tray icon started")
            else:
                # Tray icon already exists, just return it
                print("System tray icon already running")

            return self._tray_icon

        except ImportError:
            print("pystray or PIL not available. System tray disabled.")
            return None
        except Exception as e:
            print(f"Error creating system tray: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_app_path(self) -> str:
        """Get the path to the current application executable."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return sys.executable
        else:
            # Running as script - return Python interpreter with module path
            python_exe = sys.executable
            module_path = str(Path(__file__).parent.parent / "main.py")
            return f'"{python_exe}" -m src.main'


# Global system integration instance
system_integration = SystemIntegration()
