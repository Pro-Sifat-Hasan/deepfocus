"""
DeepFocus - Main application entry point.
"""
import flet as ft
import sys
import os
import asyncio
from pathlib import Path

# Fix imports for both development and packaged modes
# When Flet packages the app, code is extracted to AppData/.../flet/app/
# We need to ensure the package structure is recognized correctly

# Get the directory containing this file
_current_file = Path(__file__).resolve()
_current_dir = _current_file.parent

# In packaged mode, files are in flet/app/ directory
# We need to make Python recognize this as a package structure
# Add parent directory to sys.path so we can import as a package
_parent_dir = _current_dir.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

# Also add current directory
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

# Create a fake package structure for relative imports to work
# When Flet packages, files are in flet/app/, but we need them to be recognized as 'app' package
# Set __package__ and __name__ correctly
if not hasattr(sys.modules.get('__main__', None), '__package__') or sys.modules['__main__'].__package__ is None:
    # Determine package name from path
    # If in flet/app/, package should be 'app'
    # If in src/, package should be 'src'
    if 'flet' in str(_current_dir) and _current_dir.name == 'app':
        # Packaged mode: files are in flet/app/
        _package_name = 'app'
    elif _current_dir.name == 'src':
        # Development mode: files are in src/
        _package_name = 'src'
    else:
        # Try to detect from path
        parts = _current_dir.parts
        if 'app' in parts:
            _package_name = 'app'
        elif 'src' in parts:
            _package_name = 'src'
        else:
            _package_name = None
    
    if _package_name:
        # Set the package for this module
        import types
        if '__main__' in sys.modules:
            main_module = sys.modules['__main__']
            main_module.__package__ = _package_name
            main_module.__name__ = f"{_package_name}.main"

# Try relative imports first (for development: python -m src.main)
try:
    from .ui.login_page import create_login_page
    from .ui.main_page import MainPage
    from .ui.custom_domain_page import CustomDomainPage
    from .ui.settings_page import SettingsPage
    from .utils.language import lang
    from .utils.system_integration import system_integration
    from .core.blocker import Blocker
    from .config.colors import PRIMARY, WARNING, ERROR
    from .config.settings import settings
except (ImportError, ValueError, SystemError):
    # Fallback: Use absolute imports with proper package setup
    # We'll import using the package name we detected
    try:
        if _package_name == 'app':
            # Packaged mode: import from app package
            from app.ui.login_page import create_login_page
            from app.ui.main_page import MainPage
            from app.ui.custom_domain_page import CustomDomainPage
            from app.ui.settings_page import SettingsPage
            from app.utils.language import lang
            from app.utils.system_integration import system_integration
            from app.core.blocker import Blocker
            from app.config.colors import PRIMARY, WARNING, ERROR
            from app.config.settings import settings
        else:
            # Development mode: import from src package
            from src.ui.login_page import create_login_page
            from src.ui.main_page import MainPage
            from src.ui.custom_domain_page import CustomDomainPage
            from src.ui.settings_page import SettingsPage
            from src.utils.language import lang
            from src.utils.system_integration import system_integration
            from src.core.blocker import Blocker
            from src.config.colors import PRIMARY, WARNING, ERROR
            from src.config.settings import settings
    except ImportError:
        # Last resort: dynamically import and patch all modules with proper package structure
        import importlib.util
        import types
        
        # Determine package name for submodules
        _subpackage = 'app' if 'flet' in str(_current_dir) else 'src'
        
        # Create fake package modules in sys.modules so relative imports work
        def _create_package_modules():
            """Create empty package modules in sys.modules."""
            packages = [
                _subpackage,
                f"{_subpackage}.config",
                f"{_subpackage}.utils",
                f"{_subpackage}.core",
                f"{_subpackage}.ui",
                f"{_subpackage}.ui.components",
            ]
            for pkg_name in packages:
                if pkg_name not in sys.modules:
                    pkg_module = types.ModuleType(pkg_name)
                    pkg_module.__package__ = pkg_name
                    pkg_module.__name__ = pkg_name
                    pkg_module.__path__ = []
                    sys.modules[pkg_name] = pkg_module
        
        def _import_and_patch_module(module_path, full_module_name, package_name):
            """Import a module and patch it so relative imports work."""
            file_path = _current_dir / module_path
            if not file_path.exists():
                raise ImportError(f"Module file not found: {file_path}")
            
            # Create parent packages first
            _create_package_modules()
            
            spec = importlib.util.spec_from_file_location(full_module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                # CRITICAL: Set __package__ BEFORE executing module
                # This allows relative imports to work
                module.__package__ = package_name
                module.__name__ = full_module_name
                # Add to sys.modules BEFORE exec so nested imports can find it
                sys.modules[full_module_name] = module
                # Execute the module
                spec.loader.exec_module(module)
                return module
            raise ImportError(f"Could not load module from {file_path}")
        
        try:
            # Import dependencies first (in dependency order)
            # Config modules (no dependencies on other custom modules)
            _import_and_patch_module("config/constants.py", f"{_subpackage}.config.constants", f"{_subpackage}.config")
            _import_and_patch_module("config/colors.py", f"{_subpackage}.config.colors", f"{_subpackage}.config")
            _import_and_patch_module("config/settings.py", f"{_subpackage}.config.settings", f"{_subpackage}.config")
            
            # Core modules (depend on config)
            _import_and_patch_module("core/hosts_manager.py", f"{_subpackage}.core.hosts_manager", f"{_subpackage}.core")
            _import_and_patch_module("core/auth.py", f"{_subpackage}.core.auth", f"{_subpackage}.core")
            _import_and_patch_module("core/blocker.py", f"{_subpackage}.core.blocker", f"{_subpackage}.core")
            _import_and_patch_module("core/protection_monitor.py", f"{_subpackage}.core.protection_monitor", f"{_subpackage}.core")
            
            # Utils modules
            _import_and_patch_module("utils/validators.py", f"{_subpackage}.utils.validators", f"{_subpackage}.utils")
            _import_and_patch_module("utils/language.py", f"{_subpackage}.utils.language", f"{_subpackage}.utils")
            _import_and_patch_module("utils/system_integration.py", f"{_subpackage}.utils.system_integration", f"{_subpackage}.utils")
            
            # UI components (depend on utils and config)
            _import_and_patch_module("ui/components/footer.py", f"{_subpackage}.ui.components.footer", f"{_subpackage}.ui.components")
            _import_and_patch_module("ui/components/platform_card.py", f"{_subpackage}.ui.components.platform_card", f"{_subpackage}.ui.components")
            
            # UI pages (depend on everything above)
            login_page_mod = _import_and_patch_module("ui/login_page.py", f"{_subpackage}.ui.login_page", f"{_subpackage}.ui")
            create_login_page = login_page_mod.create_login_page
            
            main_page_mod = _import_and_patch_module("ui/main_page.py", f"{_subpackage}.ui.main_page", f"{_subpackage}.ui")
            MainPage = main_page_mod.MainPage
            
            custom_page_mod = _import_and_patch_module("ui/custom_domain_page.py", f"{_subpackage}.ui.custom_domain_page", f"{_subpackage}.ui")
            CustomDomainPage = custom_page_mod.CustomDomainPage
            
            settings_page_mod = _import_and_patch_module("ui/settings_page.py", f"{_subpackage}.ui.settings_page", f"{_subpackage}.ui")
            SettingsPage = settings_page_mod.SettingsPage
            
            # Get required objects from loaded modules
            lang = sys.modules[f"{_subpackage}.utils.language"].lang
            system_integration = sys.modules[f"{_subpackage}.utils.system_integration"].system_integration
            Blocker = sys.modules[f"{_subpackage}.core.blocker"].Blocker
            colors_mod = sys.modules[f"{_subpackage}.config.colors"]
            PRIMARY = colors_mod.PRIMARY
            WARNING = colors_mod.WARNING
            ERROR = colors_mod.ERROR
            settings = sys.modules[f"{_subpackage}.config.settings"].settings
        except Exception as e:
            import traceback
            error_msg = f"Critical import error: {e}\n{traceback.format_exc()}"
            print(error_msg)
            raise ImportError(f"Failed to import required modules. Original error: {e}")


class App: 
    """Main application class."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "DeepFocus"
        
        # Set window properties FIRST before any content
        self.page.window.width = 800
        self.page.window.height = 700  
        self.page.window.min_width = 600
        self.page.window.min_height = 500 
        self.page.window.resizable = True    
         
        # Prevent window from closing - app always runs  
        self.page.window.prevent_close = True   
           
        # Handle window close event - minimize to tray instead of closing
        def on_window_event(e):
            if hasattr(e, 'data') and e.data == "close":
                # Hide window instead of closing - app keeps running in tray
                self.page.window.visible = False
                self.page.update()
                print("Window hidden - app running in system tray")
        
        try:
            self.page.window.on_event = on_window_event
        except:
            pass  # Fallback if event handler not available
        
        # Store reference to app instance for tray callbacks
        self.app_instance = self
          
        # Set theme
        self.page.theme_mode = ft.ThemeMode.SYSTEM 
        
        # Configure fonts for Bengali support
        self.page.fonts = {
            "NotoSansBengali": "https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;600;700&display=swap"
        }
        
        # Set theme with primary color (Niagara)
        # PRIMARY is already imported at top 
        self.page.theme = ft.Theme(
            font_family="Segoe UI", 
            color_scheme_seed=PRIMARY,
        )
        
        # Set background color to match theme
        # Background will be set by theme system
        
        # Current page state
        self.current_page = None
        self.is_logged_in = False
        
        # Initialize language
        lang.set_language(lang.get_current_language())
        
        # Setup navigation handler
        self.page.on_navigate = self._handle_navigation
        
        # Show login page immediately - Flet will handle window visibility
        self._show_login_page()
        
        # Check admin privileges after UI is shown
        try:
            blocker = Blocker()
            if not blocker.is_admin():
                self._show_admin_warning()
            else:
                # Start advanced protection if admin
                try:
                    from .core.protection_monitor import protection_monitor
                except ImportError:
                    # Already imported in fallback, get from sys.modules
                    _pkg = 'app' if 'flet' in str(Path(__file__).parent) else 'src'
                    prot_mon_mod = sys.modules.get(f"{_pkg}.core.protection_monitor")
                    if prot_mon_mod and hasattr(prot_mon_mod, 'protection_monitor'):
                        protection_monitor = prot_mon_mod.protection_monitor
                    else:
                        # Import protection_monitor now
                        try:
                            from src.core.protection_monitor import protection_monitor
                        except ImportError:
                            from app.core.protection_monitor import protection_monitor
                protection_monitor.start()
                
                # Start DNS-level blocking (optional, can be enabled via settings)
                # from .core.dns_blocker import dns_blocker
                # dns_blocker.start()
                
                # Start process blocking (optional, can be enabled via settings)
                # from .core.process_blocker import process_blocker
                # process_blocker.start()
                
                # Protect hosts file
                protection_monitor.protect_hosts_file()
                
                # Setup system tray for background operation
                try:
                    setup_system_tray(self)
                    print("System tray icon created - app will minimize to tray when closed")
                except Exception as e:
                    print(f"Error setting up system tray: {e}")
        except Exception as e:
            print(f"Error checking admin privileges: {e}")
        
        # Always enable auto-start - app should always run
        # Ensure settings and system_integration are available
        try:
            # Try to use the imported variables (may not be in function scope)
            _ = system_integration
            _ = settings
        except NameError:
            # Not available, import them
            try:
                from .config.settings import settings
                from .utils.system_integration import system_integration
            except ImportError:
                try:
                    from src.config.settings import settings
                    from src.utils.system_integration import system_integration
                except ImportError:
                    from app.config.settings import settings
                    from app.utils.system_integration import system_integration
        
        # Now use them safely
        try:
            app_path = system_integration.get_app_path()
            system_integration.set_auto_start(True, app_path)  
            if not settings.is_auto_start(): 
                settings.set_auto_start(True)
        except Exception as e:
            print(f"Warning: Could not set auto-start: {e}")

    def _show_login_page(self) -> None:
        """Show login page."""
        try:
            self.is_logged_in = False
            login_container = create_login_page(self.page, self._on_login_success)
            
            # Clear and add content immediately
            self.page.controls.clear()
            self.page.add(login_container)
            
            # Update page to render content
            self.page.update()
        except Exception as e:
            print(f"Error showing login page: {e}")
            import traceback
            traceback.print_exc()
            # Show error page
            self.page.controls.clear()
            self.page.add(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Error loading application", size=24, color=WARNING),
                            ft.Text(str(e), size=12),
                        ],
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                )
            )
            self.page.update()

    def _on_login_success(self) -> None:
        """Handle successful login."""
        self.is_logged_in = True
        
        # CRITICAL: Apply blocking immediately after login
        print("[App] Login successful - applying blocking immediately...")
        try:
            blocker = Blocker()
            if blocker.is_admin():
                print("[App] Admin privileges detected - applying all blocking...")
                blocker.sync_with_hosts_file()
                
                # Force apply adult content and casino/gambling blocking
                # settings should already be imported at top - use try/except to avoid scope issues
                try:
                    # Try to use the imported settings
                    _ = settings.is_adult_content_blocked
                except NameError:
                    # Not available, import it
                    try:
                        from .config.settings import settings
                    except ImportError:
                        try:
                            from src.config.settings import settings
                        except ImportError:
                            from app.config.settings import settings
                
                try:
                    from .config.constants import ADULT_CONTENT_DOMAINS, CASINO_GAMBLING_DOMAINS
                except ImportError:
                    try:
                        from src.config.constants import ADULT_CONTENT_DOMAINS, CASINO_GAMBLING_DOMAINS
                    except ImportError:
                        from app.config.constants import ADULT_CONTENT_DOMAINS, CASINO_GAMBLING_DOMAINS
                
                # Block adult content if enabled - use blocker method for proper cleanup
                if settings.is_adult_content_blocked():
                    print(f"[App] Applying adult content blocking ({len(ADULT_CONTENT_DOMAINS)} domains)...")
                    success = blocker.block_adult_content()
                    if success:
                        blocked_domains = blocker.hosts_manager.get_blocked_domains()
                        blocked_count = sum(1 for domain in ADULT_CONTENT_DOMAINS if domain in blocked_domains)
                        print(f"[App] ✓ Adult content: {blocked_count}/{len(ADULT_CONTENT_DOMAINS)} domains blocked")
                    else:
                        print("[App] ✗ Failed to apply adult content blocking")
                
                # Block casino/gambling if enabled - use blocker method for proper cleanup
                if settings.is_casino_gambling_blocked():
                    print(f"[App] Applying casino/gambling blocking ({len(CASINO_GAMBLING_DOMAINS)} domains)...")
                    success = blocker.block_casino_gambling()
                    if success:
                        blocked_domains = blocker.hosts_manager.get_blocked_domains()
                        blocked_count = sum(1 for domain in CASINO_GAMBLING_DOMAINS if domain in blocked_domains)
                        print(f"[App] ✓ Casino/gambling: {blocked_count}/{len(CASINO_GAMBLING_DOMAINS)} domains blocked")
                    else:
                        print("[App] ✗ Failed to apply casino/gambling blocking")
            else:
                print("[App] WARNING: Not running as Administrator - blocking will not work!")
        except Exception as e:
            print(f"[App] Error applying blocking after login: {e}")
            import traceback
            traceback.print_exc()
        
        self._navigate_to_main()

    def _show_main_page(self) -> None:
        """Show main dashboard page."""
        try:
            print("Creating MainPage instance...")
            main_page = MainPage(self.page)
            self.current_page = "main"
            print("Creating main page container...")
            main_container = main_page.create_page()
            print(f"Main container created: {type(main_container)}")
            self.page.controls.clear()
            self.page.add(main_container)
            print("Updating page...")
            self.page.update()
            print("Main page displayed successfully")
        except Exception as e:
            print(f"Error showing main page: {e}")
            import traceback
            traceback.print_exc()
            # Show error message
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error loading main page: {str(e)}"),
                bgcolor=WARNING,
                duration=5000,
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _show_custom_domains_page(self) -> None:
        """Show custom domains page."""
        try:
            print("[App] Starting _show_custom_domains_page()...")
            print("[App] Creating CustomDomainPage instance...")
            custom_page = CustomDomainPage(self.page)
            print("[App] CustomDomainPage instance created")
            
            self.current_page = "custom_domains"
            print(f"[App] Current page set to: {self.current_page}")
            
            print("[App] Calling create_page()...")
            custom_container = custom_page.create_page()
            print(f"[App] Container created: {type(custom_container)}")
            
            print("[App] Clearing page controls...")
            self.page.controls.clear()
            print("[App] Page controls cleared")
            
            print("[App] Adding custom container to page...")
            self.page.add(custom_container)
            print("[App] Container added to page") 
            
            print("[App] Updating page...")
            self.page.update()
            print("[App] Page updated successfully")
            
            # Force refresh of domain list after page is displayed to ensure it renders
            print("[App] Triggering domain list refresh after page display...")
            try:
                if hasattr(custom_page, '_refresh_domain_list'):
                    custom_page._refresh_domain_list()
                    print("[App] Domain list refreshed after page display")
                    self.page.update()
                    print("[App] Page updated again after domain list refresh")
            except Exception as refresh_err:
                print(f"[App] Note: Could not refresh domain list after display: {refresh_err}")
            
            print("[App] Custom domains page displayed successfully")
            
        except Exception as e:
            print(f"[App] ERROR showing custom domains page: {e}")
            import traceback
            traceback.print_exc()
            # Show error message
            try:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error loading custom domains page: {str(e)}"),
                    bgcolor=WARNING,
                    duration=5000,
                ) 
                self.page.snack_bar.open = True
                self.page.update() 
            except:  
                pass

    def _show_settings_page(self) -> None:  
        """Show settings page.""" 
        settings_page = SettingsPage(self.page) 
        self.current_page = "settings" 
        settings_container = settings_page.create_page()
        self.page.controls.clear()
        self.page.add(settings_container)
        self.page.update()
     
    def _refresh_current_page(self) -> None: 
        """Refresh the current page to apply language changes."""
        if self.current_page == "settings":
            self._show_settings_page()
        elif self.current_page == "main":  
            self._show_main_page()
        elif self.current_page == "custom_domains":
            self._show_custom_domains_page()

    def _handle_navigation(self, route: str) -> None:
        """Handle navigation between pages."""
        if route == "main":
            self._show_main_page()
        elif route == "custom_domains":
            self._show_custom_domains_page()
        elif route == "settings":
            self._show_settings_page()

    def _navigate_to_main(self) -> None:
        """Navigate to main page."""
        self._handle_navigation("main")

    def _show_admin_warning(self) -> None:
        """Show warning about admin privileges."""
        # Show a banner or notification about admin requirements
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(lang.translate("admin_required_msg")),
            bgcolor=WARNING,
            duration=5000,
        )
        self.page.snack_bar.open = True
        self.page.update()
    


async def main(page: ft.Page):
    """Main entry point for Flet app."""
    try:
        # Check if app should start minimized (for auto-start)
        # Check command line arguments or environment variable
        import sys
        start_minimized = "--minimized" in sys.argv or os.getenv("DEEPFOCUS_MINIMIZED", "").lower() == "true"
        
        # Initialize app (content will be added)
        app = App(page)
        
        # Wait a brief moment for content to render
        import asyncio
        await asyncio.sleep(0.1)
        
        # Center window (async)
        await page.window.center()
        
        # Show window unless starting minimized
        if not start_minimized:
            page.window.visible = True
            page.update()
            print("App started - window visible")
        else:
            page.window.visible = False
            page.update()
            print("App started - running in system tray (minimized)")
        
    except Exception as e:
        print(f"Fatal error initializing app: {e}")
        import traceback
        traceback.print_exc()
        # Try to show error on page
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
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                    padding=40,
                )
            )
            page.window.visible = True
            page.update()
        except:
            pass


def setup_system_tray(app_instance):
    """Setup system tray icon."""
    def show_window():
        # Show window
        app_instance.page.window.visible = True
        app_instance.page.update()

    def quit_app():
        # App cannot be quit - just hide window (keeps running in background)
        app_instance.page.window.visible = False
        app_instance.page.update()
        # Optionally show notification that app is still running
        try:
            app_instance.page.snack_bar = ft.SnackBar(
                content=ft.Text("App is still running in background. Right-click tray icon to show."),
                duration=3000,
            )
            app_instance.page.snack_bar.open = True
            app_instance.page.update()
        except:
            pass

    # Ensure system_integration is available
    try:
        _ = system_integration
    except NameError:
        # Not available, import it
        try:
            from .utils.system_integration import system_integration
        except ImportError:
            try:
                from src.utils.system_integration import system_integration
            except ImportError:
                from app.utils.system_integration import system_integration

    icon_path = Path(__file__).parent / "assets" / "icon.ico"
    
    try:
        system_integration.create_system_tray(
            icon_path=str(icon_path) if icon_path.exists() else None,
            show_callback=show_window,
            quit_callback=quit_app,
            menu_title="DeepFocus",
        )
    except Exception as e:
        print(f"Error setting up system tray: {e}")


if __name__ == "__main__":
    # Always enable auto-start - app should always run
    # Ensure settings and system_integration are available
    try:
        # Try to use the imported variables
        _ = system_integration
        _ = settings
    except NameError:
        # Not available, import them
        try:
            from .config.settings import settings
            from .utils.system_integration import system_integration
        except ImportError:
            try:
                from src.config.settings import settings
                from src.utils.system_integration import system_integration
            except ImportError:
                from app.config.settings import settings
                from app.utils.system_integration import system_integration
    
    # Now use them safely
    try:
        app_path = system_integration.get_app_path()
        system_integration.set_auto_start(True, app_path)
        settings.set_auto_start(True)
    except Exception as e:
        print(f"Warning: Could not set auto-start: {e}")
    
    # Run the Flet app
    # Note: When using 'flet run -m src.main', Flet CLI calls ft.run() automatically
    # This ft.run() is only for direct Python execution: python -m src.main
    ft.run(main)
