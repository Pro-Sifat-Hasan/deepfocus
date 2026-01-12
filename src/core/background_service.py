"""
Background service manager - ensures app always runs and cannot be closed.
"""
import sys
import subprocess
import time
import threading
from pathlib import Path


class BackgroundService:
    """Manages app as always-running background service."""
    
    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.app_process = None
        
    def start_monitoring(self) -> None:
        """Start monitoring and auto-restart if app closes."""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("Background service: Started monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring."""
        self.running = False
    
    def _monitor_loop(self) -> None:
        """Monitor app process and restart if needed."""
        while self.running:
            try:
                # Check if main process is still running
                # In a real implementation, you'd check the process ID
                time.sleep(5)
            except Exception as e:
                print(f"Background service monitor error: {e}")
    
    def prevent_close(self, page) -> None:
        """Prevent window from closing."""
        def on_window_event(e):
            if e.data == "close":
                # Prevent closing - hide window instead
                page.window.visible = False
                page.update()
        
        # Intercept window close events
        # Note: Flet doesn't expose window close event directly
        # This would need to be handled at a lower level
        pass


# Global background service instance
background_service = BackgroundService()
