"""
DeepFocus - Main application entry point.
"""
import flet as ft
import sys
import asyncio
from pathlib import Path

from .ui.login_page import create_login_page
from .ui.main_page import MainPage
from .ui.custom_domain_page import CustomDomainPage
from .ui.settings_page import SettingsPage
from .utils.language import lang
from .utils.system_integration import system_integration
from .core.blocker import Blocker
from .config.colors import PRIMARY, WARNING, ERROR


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
           
        # Handle window events - minimize instead of close
        def on_window_event(e):
            if hasattr(e, 'data') and e.data == "close":
                # Hide window instead of closing - app keeps running
                self.page.window.visible = False
                self.page.update()
        
        try:
            self.page.window.on_event = on_window_event
        except:
            pass  # Fallback if event handler not available
          
        # Set theme
        self.page.theme_mode = ft.ThemeMode.SYSTEM 
        
        # Configure fonts for Bengali support
        self.page.fonts = {
            "NotoSansBengali": "https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;600;700&display=swap"
        }
        
        # Set theme with primary color (Niagara)
        from .config.colors import PRIMARY 
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
                from .core.protection_monitor import protection_monitor
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
                except Exception as e:
                    print(f"Error setting up system tray: {e}")
        except Exception as e:
            print(f"Error checking admin privileges: {e}")
        
        # Always enable auto-start - app should always run
        from .config.settings import settings
        from .utils.system_integration import system_integration
        app_path = system_integration.get_app_path()
        system_integration.set_auto_start(True, app_path)
        if not settings.is_auto_start():
            settings.set_auto_start(True)

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
                from .config.settings import settings
                from .config.constants import ADULT_CONTENT_DOMAINS, CASINO_GAMBLING_DOMAINS
                
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
        # Initialize app (content will be added)
        app = App(page)
        
        # Wait a brief moment for content to render
        import asyncio
        await asyncio.sleep(0.1)
        
        # Center window (async)
        await page.window.center()
        
        # Make window visible now that content is ready
        page.window.visible = True
        page.update()
        
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

    icon_path = Path(__file__).parent / "assets" / "icon.ico"
    
    system_integration.create_system_tray(
        icon_path=str(icon_path) if icon_path.exists() else None,
        show_callback=show_window,
        quit_callback=quit_app,
        menu_title="DeepFocus",
    )


if __name__ == "__main__":
    # Always enable auto-start - app should always run
    from .config.settings import settings
    app_path = system_integration.get_app_path()
    system_integration.set_auto_start(True, app_path)
    settings.set_auto_start(True)
    
    # Run the Flet app
    # Note: When using 'flet run -m src.main', Flet CLI calls ft.run() automatically
    # This ft.run() is only for direct Python execution: python -m src.main
    ft.run(main)
