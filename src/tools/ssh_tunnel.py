"""SSH Tunnel Manager for OCI Bastion connectivity.

Provides automated SSH tunnel management for connecting to private
OCI databases through a Bastion host.

Usage:
    from src.tools.ssh_tunnel import SSHTunnelManager
    
    tunnel = SSHTunnelManager()
    await tunnel.start()
    
    # Use database at localhost:1521
    
    await tunnel.stop()
"""
import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Optional
import logging

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class SSHTunnelManager:
    """Manages SSH tunnel to OCI Bastion for database connectivity."""
    
    def __init__(
        self,
        bastion_host: Optional[str] = None,
        bastion_user: str = "opc",
        bastion_key_path: Optional[str] = None,
        db_private_ip: Optional[str] = None,
        db_port: int = 1521,
        local_port: int = 1521,
    ):
        """Initialize the SSH tunnel manager.
        
        Args:
            bastion_host: Public IP of the Bastion host.
            bastion_user: SSH user for Bastion (default: opc).
            bastion_key_path: Path to SSH private key.
            db_private_ip: Private IP of the database server.
            db_port: Database port (default: 1521).
            local_port: Local port to forward to (default: 1521).
        """
        settings = get_settings()
        
        self.bastion_host = bastion_host or getattr(settings, 'bastion_host', None)
        self.bastion_user = bastion_user or getattr(settings, 'bastion_user', 'opc')
        self.bastion_key_path = bastion_key_path or getattr(settings, 'bastion_key_path', None)
        self.db_private_ip = db_private_ip or getattr(settings, 'db_private_ip', None)
        self.db_port = db_port or getattr(settings, 'db_port', 1521)
        self.local_port = local_port
        
        self._process: Optional[subprocess.Popen] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._retry_count = 0
        self._max_retries = 3
    
    @property
    def is_configured(self) -> bool:
        """Check if all required settings are provided."""
        return all([
            self.bastion_host,
            self.bastion_key_path,
            self.db_private_ip,
        ])
    
    @property
    def is_active(self) -> bool:
        """Check if the tunnel is currently active."""
        if self._process is None:
            return False
        return self._process.poll() is None
    
    def _build_ssh_command(self) -> list[str]:
        """Build the SSH command for the tunnel."""
        key_path = Path(self.bastion_key_path).resolve()
        
        cmd = [
            "ssh",
            "-L", f"{self.local_port}:{self.db_private_ip}:{self.db_port}",
            "-i", str(key_path),
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ServerAliveInterval=60",
            "-o", "ServerAliveCountMax=3",
            "-o", "ExitOnForwardFailure=yes",
            "-N",  # No remote command
            f"{self.bastion_user}@{self.bastion_host}",
        ]
        
        return cmd
    
    async def start(self) -> bool:
        """Start the SSH tunnel.
        
        Returns:
            True if tunnel started successfully, False otherwise.
        """
        if not self.is_configured:
            logger.error("SSH tunnel not configured. Set BASTION_HOST, BASTION_KEY_PATH, DB_PRIVATE_IP in .env")
            return False
        
        if self.is_active:
            logger.info("SSH tunnel already active")
            return True
        
        try:
            cmd = self._build_ssh_command()
            logger.info(f"Starting SSH tunnel: localhost:{self.local_port} -> {self.db_private_ip}:{self.db_port}")
            
            # Start SSH process
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            
            # Wait a moment for connection to establish
            await asyncio.sleep(2)
            
            if not self.is_active:
                stderr = self._process.stderr.read().decode() if self._process.stderr else ""
                logger.error(f"SSH tunnel failed to start: {stderr}")
                return False
            
            logger.info(f"SSH tunnel established on port {self.local_port}")
            self._retry_count = 0
            
            # Start monitor task
            self._monitor_task = asyncio.create_task(self._monitor_tunnel())
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start SSH tunnel: {e}")
            return False
    
    async def stop(self) -> None:
        """Stop the SSH tunnel."""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
            logger.info("SSH tunnel stopped")
    
    async def _monitor_tunnel(self) -> None:
        """Monitor tunnel health and auto-reconnect if needed."""
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            if not self.is_active:
                logger.warning("SSH tunnel disconnected, attempting reconnect...")
                
                if self._retry_count >= self._max_retries:
                    logger.error("Max reconnection attempts reached")
                    break
                
                self._retry_count += 1
                await asyncio.sleep(5)  # Wait before retry
                
                if await self.start():
                    logger.info("SSH tunnel reconnected successfully")
                else:
                    logger.error(f"Reconnection attempt {self._retry_count} failed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


# Global tunnel instance
_tunnel_manager: Optional[SSHTunnelManager] = None


def get_tunnel_manager() -> SSHTunnelManager:
    """Get the global SSH tunnel manager instance."""
    global _tunnel_manager
    if _tunnel_manager is None:
        _tunnel_manager = SSHTunnelManager()
    return _tunnel_manager


async def ensure_tunnel() -> bool:
    """Ensure SSH tunnel is running, start if not.
    
    Returns:
        True if tunnel is active, False if failed to start.
    """
    tunnel = get_tunnel_manager()
    
    if not tunnel.is_configured:
        logger.warning("SSH tunnel not configured - skipping")
        return True  # Allow local/direct connections
    
    if tunnel.is_active:
        return True
    
    return await tunnel.start()
