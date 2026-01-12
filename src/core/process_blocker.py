"""
Process-based blocking - Prevents specific browsers/apps from running.
"""
import subprocess
import platform
import time
import threading
from typing import Set

from ..config.settings import settings


class ProcessBlocker:
    """Blocks specific processes (browsers) from running."""
    
    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.blocked_processes = {
            # Browsers
            "chrome.exe",
            "msedge.exe",
            "firefox.exe",
            "opera.exe",
            "brave.exe",
            "vivaldi.exe",
            "safari.exe",
            # Social media apps
            "facebook.exe",
            "instagram.exe",
            "twitter.exe",
            "discord.exe",
        }
        
    def start(self) -> bool:
        """Start process monitoring and blocking."""
        if self.running:
            return True
        
        if platform.system() != "Windows":
            print("Process blocker: Windows only feature")
            return False
        
        try:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            print("Process blocker: Started")
            return True
        except Exception as e:
            print(f"Process blocker: Failed to start: {e}")
            return False
    
    def stop(self) -> None:
        """Stop process blocking."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("Process blocker: Stopped")
    
    def _monitor_loop(self) -> None:
        """Monitor and kill blocked processes."""
        while self.running:
            try:
                self._kill_blocked_processes()
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                print(f"Process blocker: Error: {e}")
                time.sleep(5)
    
    def _kill_blocked_processes(self) -> None:
        """Kill any running blocked processes."""
        try:
            # Get list of running processes
            result = subprocess.run(
                ["tasklist", "/FO", "CSV"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            for line in result.stdout.splitlines()[1:]:  # Skip header
                if not line.strip():
                    continue
                
                # Parse CSV line
                parts = line.split('","')
                if len(parts) >= 1:
                    process_name = parts[0].strip('"').lower()
                    
                    if process_name in self.blocked_processes:
                        # Kill the process
                        try:
                            pid = parts[1].strip('"') if len(parts) > 1 else None
                            if pid:
                                subprocess.run(
                                    ["taskkill", "/F", "/PID", pid],
                                    capture_output=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                                )
                                print(f"Process blocker: Killed {process_name}")
                        except Exception as e:
                            print(f"Process blocker: Error killing {process_name}: {e}")
        except Exception as e:
            print(f"Process blocker: Error checking processes: {e}")


# Global process blocker instance
process_blocker = ProcessBlocker()
