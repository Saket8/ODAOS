"""Live Database Test - READ ONLY.

This script ONLY runs SELECT queries. No INSERT, UPDATE, DELETE, or DDL.
Safe to run against production.
"""
import warnings
warnings.filterwarnings("ignore")

import sys
sys.path.insert(0, ".")

# Initialize thick mode first
import oracledb
try:
    oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_21_20")
except:
    pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

console = Console()


def main():
    console.print(Panel.fit(
        "[bold cyan]ODAOS Live Database Test[/bold cyan]\n"
        "[yellow]⚠️ READ-ONLY - No modifications[/yellow]",
        border_style="blue"
    ))
    
    # Start tunnel
    console.print("\n[bold]1. Establishing Connection[/bold]")
    from src.database.tunnel import SSHTunnelManager
    from src.core.config import get_settings
    
    tunnel = SSHTunnelManager()
    tunnel.start()
    console.print("   [green]✓ SSH Tunnel active[/green]")
    
    settings = get_settings()
    conn = oracledb.connect(
        user=settings.oracle_user,
        password=settings.oracle_password.get_secret_value(),
        dsn=settings.oracle_dsn
    )
    console.print("   [green]✓ Connected to BRMPDB[/green]")
    
    cursor = conn.cursor()
    
    try:
        # ============================================================
        # Test 1: Database Information (READ ONLY)
        # ============================================================
        console.print("\n[bold]2. Database Information[/bold]")
        
        cursor.execute("""
            SELECT name, created, open_mode, database_role 
            FROM v$database
        """)
        row = cursor.fetchone()
        if row:
            console.print(f"   Database: [cyan]{row[0]}[/cyan]")
            console.print(f"   Created: {row[1]}")
            console.print(f"   Open Mode: {row[2]}")
            console.print(f"   Role: {row[3]}")
        
        # ============================================================
        # Test 2: Performance Metrics (READ ONLY)
        # ============================================================
        console.print("\n[bold]3. Performance Metrics[/bold]")
        
        # Session count
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status='ACTIVE' THEN 1 ELSE 0 END) as active
            FROM v$session WHERE type='USER'
        """)
        row = cursor.fetchone()
        console.print(f"   Sessions: {row[0]} total, {row[1]} active")
        
        # SGA info
        cursor.execute("""
            SELECT name, ROUND(bytes/1024/1024) as mb 
            FROM v$sgainfo WHERE name IN ('Fixed SGA Size', 'Redo Buffers', 'Buffer Cache Size')
        """)
        for row in cursor:
            console.print(f"   {row[0]}: {row[1]} MB")
        
        # ============================================================
        # Test 3: Tablespace Usage (READ ONLY)
        # ============================================================
        console.print("\n[bold]4. Tablespace Usage[/bold]")
        
        table = Table(title="Tablespace Summary")
        table.add_column("Tablespace", style="cyan")
        table.add_column("Total MB", justify="right")
        table.add_column("Used %", justify="right")
        table.add_column("Status")
        
        cursor.execute("""
            SELECT ts.tablespace_name,
                   ROUND(df.total_bytes/1024/1024) as total_mb,
                   ROUND((df.total_bytes - NVL(fs.free_bytes, 0))/df.total_bytes * 100, 1) as used_pct
            FROM dba_tablespaces ts
            LEFT JOIN (SELECT tablespace_name, SUM(bytes) as total_bytes FROM dba_data_files GROUP BY tablespace_name) df 
                ON ts.tablespace_name = df.tablespace_name
            LEFT JOIN (SELECT tablespace_name, SUM(bytes) as free_bytes FROM dba_free_space GROUP BY tablespace_name) fs 
                ON ts.tablespace_name = fs.tablespace_name
            WHERE ts.contents = 'PERMANENT'
            ORDER BY used_pct DESC NULLS LAST
            FETCH FIRST 5 ROWS ONLY
        """)
        
        for row in cursor:
            pct = row[2] or 0
            status = "[green]✓ OK[/green]" if pct < 80 else "[yellow]⚠ Warning[/yellow]" if pct < 90 else "[red]✗ Critical[/red]"
            table.add_row(row[0], str(row[1] or 0), f"{pct}%", status)
        
        console.print(table)
        
        # ============================================================
        # Test 4: Top SQL (READ ONLY)
        # ============================================================
        console.print("\n[bold]5. Top SQL by Elapsed Time[/bold]")
        
        cursor.execute("""
            SELECT sql_id, 
                   ROUND(elapsed_time/1000000, 2) as elapsed_secs,
                   executions,
                   SUBSTR(sql_text, 1, 60) as sql_preview
            FROM v$sql
            WHERE executions > 0
            ORDER BY elapsed_time DESC
            FETCH FIRST 3 ROWS ONLY
        """)
        
        for i, row in enumerate(cursor, 1):
            console.print(f"   {i}. [dim]{row[0]}[/dim] - {row[1]}s ({row[2]} execs)")
            console.print(f"      [dim]{row[3]}...[/dim]")
        
        # ============================================================
        # Test 5: Check for Blocking (READ ONLY)
        # ============================================================
        console.print("\n[bold]6. Blocking Sessions Check[/bold]")
        
        cursor.execute("""
            SELECT COUNT(*) FROM v$session WHERE blocking_session IS NOT NULL
        """)
        blocking = cursor.fetchone()[0]
        
        if blocking == 0:
            console.print("   [green]✓ No blocking sessions detected[/green]")
        else:
            console.print(f"   [yellow]⚠ {blocking} blocked sessions found[/yellow]")
        
        # ============================================================
        # Final Summary
        # ============================================================
        console.print("\n" + "=" * 50)
        console.print("[bold green]✅ LIVE DATABASE TEST COMPLETE[/bold green]")
        console.print("[dim]All queries were READ-ONLY (SELECT only)[/dim]")
        console.print(f"[dim]Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
        
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
    finally:
        cursor.close()
        conn.close()
        tunnel.stop()
        console.print("[dim]Connection closed[/dim]")


if __name__ == "__main__":
    main()
