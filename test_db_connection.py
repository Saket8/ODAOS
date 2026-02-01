"""Test database connection via SSH tunnel."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel

console = Console()


async def test_connection():
    """Test database connectivity through Bastion tunnel."""
    console.print(Panel.fit(
        "[bold cyan]ODAOS Database Connection Test[/bold cyan]\n"
        "Testing connection via SSH tunnel to BRMPDB",
        border_style="blue"
    ))
    
    # Step 1: Start SSH tunnel
    console.print("\n[bold]1. Starting SSH Tunnel[/bold]")
    
    try:
        from src.database.tunnel import SSHTunnelManager
        
        tunnel = SSHTunnelManager()
        port = tunnel.start()
        console.print(f"[green]✓ Tunnel active on localhost:{port}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Tunnel failed: {e}[/red]")
        console.print("[yellow]Hint: Make sure the Bastion host is reachable and SSH key is correct[/yellow]")
        return False
    
    # Step 2: Test Oracle connection
    console.print("\n[bold]2. Testing Oracle Connection[/bold]")
    
    try:
        from src.database.connection import OracleConnectionManager
        
        manager = OracleConnectionManager()
        result = await manager.test_connection()
        
        if result.get("connected"):
            console.print("[green]✓ Database connected![/green]")
            info = result.get("database_info", {})
            console.print(f"  Version: {info.get('VERSION', 'N/A')}")
            console.print(f"  Instance: {info.get('INSTANCE_NAME', 'N/A')}")
        else:
            console.print(f"[red]✗ Connection failed: {result.get('error')}[/red]")
            tunnel.stop()
            return False
    except Exception as e:
        console.print(f"[red]✗ Connection error: {e}[/red]")
        tunnel.stop()
        return False
    
    # Step 3: Test a simple query
    console.print("\n[bold]3. Testing Query Execution[/bold]")
    
    try:
        query = "SELECT 'ODAOS Connected!' as message, SYSDATE as timestamp FROM DUAL"
        result = await manager.execute_query(query)
        
        if result:
            console.print(f"[green]✓ {result[0].get('MESSAGE')}[/green]")
            console.print(f"  Server time: {result[0].get('TIMESTAMP')}")
        
        await manager.close()
    except Exception as e:
        console.print(f"[red]✗ Query error: {e}[/red]")
    
    # Step 4: Cleanup
    console.print("\n[bold]4. Cleanup[/bold]")
    tunnel.stop()
    console.print("[green]✓ Tunnel closed[/green]")
    
    console.print("\n[bold green]✅ Database connection test PASSED![/bold green]")
    return True


if __name__ == "__main__":
    asyncio.run(test_connection())
