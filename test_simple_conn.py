"""Simple database connection test."""
import asyncio
import sys
import warnings
from pathlib import Path

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
console = Console()


async def test():
    console.print("[cyan]Testing ODAOS Database Connection[/cyan]\n")
    
    # 1. Start tunnel
    console.print("1. Starting SSH tunnel...")
    try:
        from src.database.tunnel import SSHTunnelManager
        tunnel = SSHTunnelManager()
        port = tunnel.start()
        console.print(f"   [green]✓ Tunnel on localhost:{port}[/green]")
    except Exception as e:
        console.print(f"   [red]✗ Tunnel error: {e}[/red]")
        return
    
    # 2. Test Oracle connection
    console.print("\n2. Connecting to Oracle...")
    try:
        import oracledb
        from src.core.config import get_settings
        
        settings = get_settings()
        dsn = settings.oracle_dsn
        user = settings.oracle_user
        pwd = settings.oracle_password.get_secret_value() if settings.oracle_password else ""
        
        console.print(f"   DSN: {dsn}")
        console.print(f"   User: {user}")
        
        # Use thin mode (no Oracle Client needed)
        conn = await oracledb.connect_async(
            user=user,
            password=pwd,
            dsn=dsn
        )
        console.print("   [green]✓ Connected![/green]")
        
        # Test query
        cursor = conn.cursor()
        await cursor.execute("SELECT banner FROM v$version WHERE ROWNUM = 1")
        row = await cursor.fetchone()
        if row:
            console.print(f"   Version: {row[0]}")
        
        await cursor.close()
        await conn.close()
        
    except Exception as e:
        console.print(f"   [red]✗ Oracle error: {e}[/red]")
    finally:
        tunnel.stop()
        console.print("\n3. Tunnel closed")


if __name__ == "__main__":
    asyncio.run(test())
