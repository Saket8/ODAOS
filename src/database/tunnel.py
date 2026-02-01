"""SSH Tunnel Manager for Bastion-based database access.

Establishes SSH tunnel through OCI Bastion to reach private database.
"""
import os
import subprocess
import time
from pathlib import Path

from sshtunnel import SSHTunnelForwarder

from src.core.config import get_settings


class SSHTunnelManager:
    """Manages SSH tunnel to database through Bastion host."""
    
    def __init__(self):
        """Initialize tunnel manager with settings."""
        settings = get_settings()
        
        self.bastion_host = settings.bastion_host
        self.bastion_user = settings.bastion_user
        self.bastion_key = settings.bastion_key_path
        self.db_private_ip = settings.db_private_ip
        self.db_port = settings.db_port
        self.local_port = getattr(settings, 'local_port', 1521)
        
        self._tunnel: SSHTunnelForwarder = None
    
    def start(self) -> int:
        """Start SSH tunnel and return local port.
        
        Returns:
            Local port number that forwards to the database.
        """
        if self._tunnel and self._tunnel.is_active:
            return self._tunnel.local_bind_port
        
        if not all([self.bastion_host, self.bastion_key, self.db_private_ip]):
            raise ValueError(
                "SSH tunnel configuration incomplete. "
                "Set BASTION_HOST, BASTION_KEY_PATH, DB_PRIVATE_IP in .env"
            )
        
        # Ensure key file exists
        key_path = Path(self.bastion_key).expanduser()
        if not key_path.exists():
            raise FileNotFoundError(f"SSH key not found: {key_path}")
        
        self._tunnel = SSHTunnelForwarder(
            (self.bastion_host, 22),
            ssh_username=self.bastion_user,
            ssh_pkey=str(key_path),
            remote_bind_address=(self.db_private_ip, self.db_port),
            local_bind_address=('127.0.0.1', self.local_port),
        )
        
        self._tunnel.start()
        
        # Wait for tunnel to be ready
        time.sleep(1)
        
        if not self._tunnel.is_active:
            raise RuntimeError("Failed to establish SSH tunnel")
        
        return self._tunnel.local_bind_port
    
    def stop(self):
        """Stop the SSH tunnel."""
        if self._tunnel:
            self._tunnel.stop()
            self._tunnel = None
    
    def is_active(self) -> bool:
        """Check if tunnel is active."""
        return self._tunnel is not None and self._tunnel.is_active
    
    @property
    def local_bind_port(self) -> int:
        """Get the local port for database connection."""
        if self._tunnel:
            return self._tunnel.local_bind_port
        return self.local_port
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# Global tunnel manager
_tunnel_manager: SSHTunnelManager = None


def get_tunnel_manager() -> SSHTunnelManager:
    """Get global tunnel manager instance."""
    global _tunnel_manager
    if _tunnel_manager is None:
        _tunnel_manager = SSHTunnelManager()
    return _tunnel_manager


def start_tunnel() -> int:
    """Start SSH tunnel and return local port."""
    return get_tunnel_manager().start()


def stop_tunnel():
    """Stop SSH tunnel."""
    get_tunnel_manager().stop()


if __name__ == "__main__":
    # Quick test
    from rich.console import Console
    console = Console()
    
    console.print("[cyan]Starting SSH tunnel to Bastion...[/cyan]")
    
    try:
        manager = SSHTunnelManager()
        port = manager.start()
        console.print(f"[green]✓ Tunnel active on localhost:{port}[/green]")
        console.print("[dim]Press Ctrl+C to stop...[/dim]")
        
        while manager.is_active():
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping tunnel...[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        manager.stop()
        console.print("[green]Tunnel stopped.[/green]")
