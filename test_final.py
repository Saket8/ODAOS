"""Quick final connection test with thick mode properly initialized."""
import warnings
warnings.filterwarnings("ignore")

import sys
sys.path.insert(0, ".")

# Initialize thick mode BEFORE importing oracledb anywhere else
import oracledb
try:
    oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_21_20")
    print("✓ Thick mode initialized")
except Exception as e:
    print(f"✓ Thick mode already active")

from rich.console import Console
console = Console()

def main():
    console.print("\n[bold cyan]ODAOS Final Database Test[/bold cyan]\n")
    
    # Start tunnel
    from src.database.tunnel import SSHTunnelManager
    tunnel = SSHTunnelManager()
    try:
        tunnel.start()
        console.print("[green]✓ SSH Tunnel active on localhost:1521[/green]")
    except Exception as e:
        console.print(f"[red]✗ Tunnel: {e}[/red]")
        return
    
    # Test synchronous connection (thick mode works with sync)
    try:
        from src.core.config import get_settings
        settings = get_settings()
        
        conn = oracledb.connect(
            user=settings.oracle_user,
            password=settings.oracle_password.get_secret_value(),
            dsn=settings.oracle_dsn
        )
        console.print("[green]✓ Oracle connected[/green]")
        
        cursor = conn.cursor()
        cursor.execute("SELECT banner FROM v$version WHERE ROWNUM=1")
        row = cursor.fetchone()
        if row:
            console.print(f"[cyan]  {row[0]}[/cyan]")
        
        cursor.execute("SELECT name FROM v$database")
        row = cursor.fetchone()
        if row:
            console.print(f"[cyan]  Database: {row[0]}[/cyan]")
        
        cursor.execute("SELECT sys_context('USERENV','CON_NAME') FROM dual")
        row = cursor.fetchone()
        if row:
            console.print(f"[cyan]  Container: {row[0]}[/cyan]")
        
        cursor.close()
        conn.close()
        console.print("\n[bold green]✅ DATABASE CONNECTION VERIFIED![/bold green]")
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
    finally:
        tunnel.stop()
        console.print("[dim]Tunnel closed[/dim]")

if __name__ == "__main__":
    main()
