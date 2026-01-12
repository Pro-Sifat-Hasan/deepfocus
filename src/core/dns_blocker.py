"""
DNS-level blocking proxy server - Advanced blocking mechanism.
This provides much stronger blocking than hosts file alone.
"""
import socket
import threading
import subprocess
import platform
from typing import Set, Optional
from pathlib import Path

from ..config.constants import PLATFORM_DOMAINS, ADULT_CONTENT_DOMAINS
from ..config.settings import settings


class DNSBlocker:
    """DNS proxy server that blocks domains at DNS level."""
    
    def __init__(self):
        self.running = False
        self.server_thread = None
        self.dns_server = "127.0.0.1"
        self.dns_port = 5353  # Local DNS port
        self.blocked_domains: Set[str] = set()
        self.socket = None
        
    def start(self) -> bool:
        """Start DNS blocking server."""
        if self.running:
            return True
        
        if platform.system() != "Windows":
            print("DNS blocker: Windows only feature")
            return False
        
        try:
            # Update blocked domains
            self._update_blocked_domains()
            
            # Start DNS server in background thread
            self.running = True
            self.server_thread = threading.Thread(target=self._dns_server_loop, daemon=True)
            self.server_thread.start()
            
            # Set Windows DNS to use our local server
            self._set_dns_server()
            
            print("DNS blocker: Started successfully")
            return True
        except Exception as e:
            print(f"DNS blocker: Failed to start: {e}")
            return False
    
    def stop(self) -> None:
        """Stop DNS blocking server."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        # Restore original DNS
        self._restore_dns_server()
        print("DNS blocker: Stopped")
    
    def _update_blocked_domains(self) -> None:
        """Update list of blocked domains from settings."""
        self.blocked_domains.clear()
        
        # Add platform domains
        for platform_name, domains in PLATFORM_DOMAINS.items():
            if settings.is_platform_blocked(platform_name):
                self.blocked_domains.update(domains)
        
        # Add adult content domains
        if settings.is_adult_content_blocked():
            self.blocked_domains.update(ADULT_CONTENT_DOMAINS)
        
        # Add custom domains
        custom_domains = settings.get_custom_domains()
        self.blocked_domains.update(custom_domains)
    
    def _is_blocked(self, domain: str) -> bool:
        """Check if domain is blocked."""
        domain = domain.lower().strip()
        if not domain:
            return False
        
        # Check exact match
        if domain in self.blocked_domains:
            return True
        
        # Check subdomain matches (e.g., www.facebook.com if facebook.com is blocked)
        for blocked in self.blocked_domains:
            if domain.endswith(f".{blocked}") or domain == blocked:
                return True
        
        return False
    
    def _dns_server_loop(self) -> None:
        """DNS server main loop - responds with NXDOMAIN for blocked domains."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((self.dns_server, self.dns_port))
            self.socket.settimeout(1.0)
            
            print(f"DNS blocker: Listening on {self.dns_server}:{self.dns_port}")
            
            while self.running:
                try:
                    data, addr = self.socket.recvfrom(512)
                    # Simple DNS query parser - extract domain
                    # This is a simplified version - for production, use dnslib
                    try:
                        # Basic DNS query parsing
                        query_id = data[0:2]
                        domain = self._parse_dns_query(data)
                        
                        if domain and self._is_blocked(domain):
                            # Return NXDOMAIN (domain not found)
                            response = self._create_nxdomain_response(query_id, data)
                            self.socket.sendto(response, addr)
                            print(f"DNS blocker: Blocked {domain}")
                        else:
                            # Forward to real DNS server
                            self._forward_dns_query(data, addr)
                    except Exception as e:
                        print(f"DNS blocker: Error processing query: {e}")
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"DNS blocker: Error in server loop: {e}")
        except Exception as e:
            print(f"DNS blocker: Server error: {e}")
        finally:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
    
    def _parse_dns_query(self, data: bytes) -> Optional[str]:
        """Parse domain name from DNS query."""
        try:
            # Skip header (12 bytes)
            if len(data) < 12:
                return None
            
            pos = 12
            domain_parts = []
            
            while pos < len(data) and data[pos] != 0:
                length = data[pos]
                if length == 0 or pos + length >= len(data):
                    break
                pos += 1
                part = data[pos:pos+length].decode('utf-8', errors='ignore')
                domain_parts.append(part)
                pos += length
            
            if domain_parts:
                return '.'.join(domain_parts)
        except Exception:
            pass
        return None
    
    def _create_nxdomain_response(self, query_id: bytes, query: bytes) -> bytes:
        """Create NXDOMAIN DNS response."""
        # Simplified NXDOMAIN response
        # Header: ID (2) + Flags (2) + Questions (2) + Answers (2) + Authority (2) + Additional (2)
        flags = b'\x81\x83'  # Response + Authoritative + NXDOMAIN
        questions = query[4:6]
        answers = b'\x00\x00'
        authority = b'\x00\x00'
        additional = b'\x00\x00'
        
        response = query_id + flags + questions + answers + authority + additional + query[12:]
        return response
    
    def _forward_dns_query(self, data: bytes, addr: tuple) -> None:
        """Forward DNS query to real DNS server (8.8.8.8)."""
        try:
            # Forward to Google DNS
            forward_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            forward_socket.settimeout(2.0)
            forward_socket.sendto(data, ("8.8.8.8", 53))
            response, _ = forward_socket.recvfrom(512)
            forward_socket.close()
            
            # Send response back to client
            if self.socket:
                self.socket.sendto(response, addr)
        except Exception as e:
            print(f"DNS blocker: Forward error: {e}")
    
    def _set_dns_server(self) -> None:
        """Set Windows DNS to use our local server."""
        try:
            # Get active network interface
            result = subprocess.run(
                ["netsh", "interface", "show", "interface"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            # Set DNS to localhost
            # This is a simplified version - in production, you'd want to be more specific
            subprocess.run(
                ["netsh", "interface", "ip", "set", "dns", "name=\"Ethernet\"", "static", self.dns_server],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        except Exception as e:
            print(f"DNS blocker: Error setting DNS: {e}")
    
    def _restore_dns_server(self) -> None:
        """Restore original DNS server settings."""
        try:
            subprocess.run(
                ["netsh", "interface", "ip", "set", "dns", "name=\"Ethernet\"", "dhcp"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        except Exception as e:
            print(f"DNS blocker: Error restoring DNS: {e}")


# Global DNS blocker instance
dns_blocker = DNSBlocker()
