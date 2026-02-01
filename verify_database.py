"""Database Connection Verification Script.

Tests SSH tunnel and Oracle database connectivity.

Usage:
    python verify_database.py
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


async def verify_configuration():
    """Verify database configuration."""
    from src.core.config import get_settings
    
    settings = get_settings()
    
    table = Table(title="Database Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Status", style="yellow")
    
    # Oracle settings
    table.add_row(
        "Oracle DSN", 
        settings.oracle_dsn or "(not set)",
        "✓" if settings.oracle_dsn else "⚠"
    )
    table.add_row(
        "Oracle User", 
        settings.oracle_user or "(not set)",
        "✓" if settings.oracle_user else "⚠"
    )
    table.add_row(
        "Oracle Password", 
        "✓ Set" if settings.oracle_password else "(not set)",
        "✓" if settings.oracle_password else "⚠"
    )
    
    # SSH Tunnel settings
    table.add_row(
        "Bastion Host", 
        settings.bastion_host or "(not set)",
        "✓" if settings.bastion_host else "─"
    )
    table.add_row(
        "DB Private IP", 
        settings.db_private_ip or "(not set)",
        "✓" if settings.db_private_ip else "─"
    )
    table.add_row(
        "Bastion Key", 
        settings.bastion_key_path or "(not set)",
        "✓" if settings.bastion_key_path and Path(settings.bastion_key_path).exists() else "─"
    )
    
    console.print(table)
    
    return bool(settings.oracle_dsn and settings.oracle_user and settings.oracle_password)


async def verify_ssh_tunnel():
    """Verify SSH tunnel can be established."""
    console.print("\n[bold]Step 2: SSH Tunnel Check[/bold]")
    
    from src.tools.ssh_tunnel import get_tunnel_manager
    
    tunnel = get_tunnel_manager()
    
    if not tunnel.is_configured:
        console.print("[yellow]SSH tunnel not configured - will use direct connection[/yellow]")
        console.print("To configure SSH tunnel, set in .env:")
        console.print("  BASTION_HOST=<public_ip>")
        console.print("  BASTION_KEY_PATH=<path_to_key>")
        console.print("  DB_PRIVATE_IP=<private_ip>")
        return True  # Skip tunnel, try direct
    
    console.print("Starting SSH tunnel...")
    
    if await tunnel.start():
        console.print("[green]✓ SSH tunnel established[/green]")
        return True
    else:
        console.print("[red]✗ SSH tunnel failed to start[/red]")
        return False


async def verify_database_connection():
    """Verify Oracle database connection."""
    console.print("\n[bold]Step 3: Database Connection Test[/bold]")
    
    from src.database.connection import OracleConnectionManager
    
    manager = OracleConnectionManager()
    
    try:
        console.print("Initializing connection pool...")
        await manager.initialize()
        console.print("[green]✓ Connection pool created[/green]")
        
        console.print("Testing database query...")
        result = await manager.test_connection()
        
        if result["connected"]:
            info = result.get("database_info", {})
            console.print("[green]✓ Database connection successful[/green]")
            
            if info:
                table = Table(title="Database Information")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")
                
                for key, value in info.items():
                    table.add_row(key.upper(), str(value))
                
                console.print(table)
            
            return True
        else:
            console.print(f"[red]✗ Connection failed: {result.get('error')}[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        return False
    finally:
        await manager.close()


async def test_sample_queries():
    """Test sample Oracle queries."""
    console.print("\n[bold]Step 4: Sample Queries[/bold]")
    
    from src.database.connection import OracleConnectionManager
    
    manager = OracleConnectionManager()
    
    try:
        await manager.initialize()
        
        # Test 1: Database version
        console.print("Testing: v$version query...")
        result = await manager.execute_query("SELECT banner FROM v$version WHERE ROWNUM = 1")
        if result:
            console.print(f"[green]✓ Version: {result[0].get('BANNER', 'Unknown')}[/green]")
        
        # Test 2: Tablespace usage
        console.print("Testing: Tablespace query...")
        result = await manager.execute_query("""
            SELECT 
                tablespace_name,
                ROUND(used_percent, 1) as used_pct
            FROM dba_tablespace_usage_metrics
            WHERE ROWNUM <= 5
            ORDER BY used_percent DESC
        """)
        
        if result:
            table = Table(title="Top Tablespaces by Usage")
            table.add_column("Tablespace", style="cyan")
            table.add_column("Used %", style="yellow")
            
            for row in result:
                pct = row.get('USED_PCT', 0)
                style = "red" if pct > 90 else "yellow" if pct > 70 else "green"
                table.add_row(row.get('TABLESPACE_NAME', ''), f"[{style}]{pct}%[/{style}]")
            
            console.print(table)
            console.print("[green]✓ Tablespace query successful[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Query error: {e}[/red]")
        return False
    finally:
        await manager.close()


async def main():
    """Main verification workflow."""
    console.print(Panel.fit(
        "[bold cyan]ODAOS Database Connection Verification[/bold cyan]\n"
        "Testing SSH tunnel and Oracle database connectivity",
        border_style="blue"
    ))
    
    results = {}
    
    # Step 1: Configuration
    console.print("\n[bold]Step 1: Verifying Configuration[/bold]")
    results["config"] = await verify_configuration()
    
    if not results["config"]:
        console.print("\n[yellow]⚠ Database not configured.[/yellow]")
        console.print("Please update .env with your database credentials:")
        console.print("  ORACLE_DSN=localhost:1521/ORCL")
        console.print("  ORACLE_USER=your_user")
        console.print("  ORACLE_PASSWORD=your_password")
        console.print("\nFor SSH tunnel (if needed):")
        console.print("  BASTION_HOST=bastion_public_ip")
        console.print("  BASTION_KEY_PATH=path/to/key.pem")
        console.print("  DB_PRIVATE_IP=db_private_ip")
        return
    
    # Step 2: SSH Tunnel
    results["tunnel"] = await verify_ssh_tunnel()
    
    # Step 3: Database Connection
    results["connection"] = await verify_database_connection()
    
    if results["connection"]:
        # Step 4: Sample Queries
        results["queries"] = await test_sample_queries()
    
    # Summary
    console.print("\n")
    summary = Table(title="Verification Summary")
    summary.add_column("Component", style="cyan")
    summary.add_column("Status", style="green")
    
    for component, status in results.items():
        summary.add_row(
            component.title(),
            "[green]✓ PASS[/green]" if status else "[red]✗ FAIL[/red]"
        )
    
    console.print(summary)
    
    if all(results.values()):
        console.print("\n[bold green]🎉 All database verifications passed![/bold green]")
    else:
        console.print("\n[bold yellow]⚠ Some verifications failed. Check logs above.[/bold yellow]")


if __name__ == "__main__":
    asyncio.run(main())
