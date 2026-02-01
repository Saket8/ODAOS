"""ODAOS Full Report CLI - Live Database.

Generates a comprehensive database health report using live data.
READ-ONLY operations only.
"""
import warnings
warnings.filterwarnings("ignore")

import sys
sys.path.insert(0, ".")

# Initialize thick mode FIRST
import oracledb
try:
    oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_21_20")
except:
    pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box
from datetime import datetime

console = Console()


def run_report():
    """Generate comprehensive database health report."""
    
    console.print(Panel.fit(
        "[bold cyan]🔮 ODAOS Full Database Health Report[/bold cyan]\n"
        "[yellow]⚠️ READ-ONLY - No modifications[/yellow]\n"
        f"[dim]Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
        border_style="blue"
    ))
    
    # Connect
    console.print("\n[bold]Connecting to Database...[/bold]")
    from src.database.tunnel import SSHTunnelManager
    from src.core.config import get_settings
    
    tunnel = SSHTunnelManager()
    tunnel.start()
    
    settings = get_settings()
    conn = oracledb.connect(
        user=settings.oracle_user,
        password=settings.oracle_password.get_secret_value(),
        dsn=settings.oracle_dsn
    )
    console.print("[green]✓ Connected via SSH tunnel[/green]")
    
    cursor = conn.cursor()
    
    try:
        # ============================================================
        # Section 1: Database Overview
        # ============================================================
        console.print("\n" + "="*60)
        console.print("[bold cyan]📊 SECTION 1: DATABASE OVERVIEW[/bold cyan]")
        console.print("="*60)
        
        cursor.execute("""
            SELECT d.name, d.created, d.open_mode, d.database_role,
                   (SELECT banner FROM v$version WHERE ROWNUM=1) as version,
                   (SELECT sys_context('USERENV','CON_NAME') FROM dual) as container
            FROM v$database d
        """)
        row = cursor.fetchone()
        
        table = Table(box=box.ROUNDED)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Database Name", row[0])
        table.add_row("Container", row[5])
        table.add_row("Created", str(row[1]))
        table.add_row("Open Mode", row[2])
        table.add_row("Role", row[3])
        table.add_row("Version", row[4].split(' - ')[0] if row[4] else "N/A")
        console.print(table)
        
        # ============================================================
        # Section 2: Performance Metrics
        # ============================================================
        console.print("\n" + "="*60)
        console.print("[bold cyan]⚡ SECTION 2: PERFORMANCE METRICS[/bold cyan]")
        console.print("="*60)
        
        # Sessions
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status='ACTIVE' THEN 1 ELSE 0 END) as active,
                   SUM(CASE WHEN status='INACTIVE' THEN 1 ELSE 0 END) as inactive
            FROM v$session WHERE type='USER'
        """)
        sess = cursor.fetchone()
        console.print(f"\n[bold]User Sessions:[/bold]")
        console.print(f"  Total: {sess[0]}  |  Active: [green]{sess[1]}[/green]  |  Inactive: {sess[2]}")
        
        # SGA
        console.print(f"\n[bold]SGA Memory Allocation:[/bold]")
        cursor.execute("""
            SELECT name, ROUND(bytes/1024/1024, 2) as mb 
            FROM v$sgainfo 
            WHERE name IN ('Fixed SGA Size', 'Redo Buffers', 'Buffer Cache Size', 
                          'Shared Pool Size', 'Large Pool Size', 'Java Pool Size')
            ORDER BY bytes DESC
        """)
        for row in cursor:
            console.print(f"  {row[0]}: [cyan]{row[1]:,.0f} MB[/cyan]")
        
        # System stats
        console.print(f"\n[bold]System Statistics:[/bold]")
        cursor.execute("""
            SELECT name, value FROM v$sysstat 
            WHERE name IN ('user commits', 'user rollbacks', 'parse count (total)', 
                          'execute count', 'physical reads', 'physical writes')
            ORDER BY value DESC
        """)
        for row in cursor:
            console.print(f"  {row[0]}: [cyan]{row[1]:,}[/cyan]")
        
        # ============================================================
        # Section 3: Tablespace Usage
        # ============================================================
        console.print("\n" + "="*60)
        console.print("[bold cyan]💾 SECTION 3: TABLESPACE USAGE[/bold cyan]")
        console.print("="*60 + "\n")
        
        table = Table(box=box.ROUNDED)
        table.add_column("Tablespace", style="cyan")
        table.add_column("Total MB", justify="right")
        table.add_column("Used MB", justify="right")
        table.add_column("Free MB", justify="right")
        table.add_column("Used %", justify="right")
        table.add_column("Status")
        
        cursor.execute("""
            SELECT ts.tablespace_name,
                   ROUND(df.total_bytes/1024/1024) as total_mb,
                   ROUND((df.total_bytes - NVL(fs.free_bytes, 0))/1024/1024) as used_mb,
                   ROUND(NVL(fs.free_bytes, 0)/1024/1024) as free_mb,
                   ROUND((df.total_bytes - NVL(fs.free_bytes, 0))/df.total_bytes * 100, 1) as used_pct
            FROM dba_tablespaces ts
            LEFT JOIN (SELECT tablespace_name, SUM(bytes) as total_bytes 
                      FROM dba_data_files GROUP BY tablespace_name) df 
                ON ts.tablespace_name = df.tablespace_name
            LEFT JOIN (SELECT tablespace_name, SUM(bytes) as free_bytes 
                      FROM dba_free_space GROUP BY tablespace_name) fs 
                ON ts.tablespace_name = fs.tablespace_name
            WHERE ts.contents = 'PERMANENT'
            ORDER BY used_pct DESC NULLS LAST
        """)
        
        alerts = []
        for row in cursor:
            pct = row[4] or 0
            if pct >= 90:
                status = "[red]✗ CRITICAL[/red]"
                alerts.append(f"[red]CRITICAL: {row[0]} at {pct}%[/red]")
            elif pct >= 80:
                status = "[yellow]⚠ WARNING[/yellow]"
                alerts.append(f"[yellow]WARNING: {row[0]} at {pct}%[/yellow]")
            else:
                status = "[green]✓ OK[/green]"
            table.add_row(
                row[0], 
                f"{row[1] or 0:,.0f}", 
                f"{row[2] or 0:,.0f}", 
                f"{row[3] or 0:,.0f}",
                f"{pct}%",
                status
            )
        console.print(table)
        
        if alerts:
            console.print("\n[bold red]⚠️ Tablespace Alerts:[/bold red]")
            for alert in alerts:
                console.print(f"  • {alert}")
        
        # ============================================================
        # Section 4: Top SQL Statements
        # ============================================================
        console.print("\n" + "="*60)
        console.print("[bold cyan]🔍 SECTION 4: TOP SQL BY ELAPSED TIME[/bold cyan]")
        console.print("="*60 + "\n")
        
        table = Table(box=box.ROUNDED)
        table.add_column("#", style="dim")
        table.add_column("SQL ID", style="cyan")
        table.add_column("Elapsed (s)", justify="right")
        table.add_column("Executions", justify="right")
        table.add_column("Buffer Gets/Exec", justify="right")
        table.add_column("Preview")
        
        cursor.execute("""
            SELECT sql_id, 
                   ROUND(elapsed_time/1000000, 2) as elapsed_secs,
                   executions,
                   ROUND(buffer_gets/NULLIF(executions,0)) as buffer_gets_per_exec,
                   SUBSTR(sql_text, 1, 50) as sql_preview
            FROM v$sql
            WHERE executions > 0
            ORDER BY elapsed_time DESC
            FETCH FIRST 10 ROWS ONLY
        """)
        
        for i, row in enumerate(cursor, 1):
            table.add_row(
                str(i),
                row[0],
                f"{row[1]:,.2f}",
                f"{row[2]:,}",
                f"{row[3] or 0:,}",
                (row[4] or "")[:40] + "..."
            )
        console.print(table)
        
        # ============================================================
        # Section 5: Blocking Session Analysis
        # ============================================================
        console.print("\n" + "="*60)
        console.print("[bold cyan]🔒 SECTION 5: BLOCKING SESSION ANALYSIS[/bold cyan]")
        console.print("="*60 + "\n")
        
        cursor.execute("""
            SELECT s1.sid as blocker_sid, s1.username as blocker_user,
                   s2.sid as blocked_sid, s2.username as blocked_user,
                   s2.seconds_in_wait, s2.event
            FROM v$session s1
            JOIN v$session s2 ON s1.sid = s2.blocking_session
            WHERE s2.blocking_session IS NOT NULL
        """)
        blockers = cursor.fetchall()
        
        if not blockers:
            console.print("[green]✓ No blocking sessions detected![/green]")
        else:
            console.print(f"[red]⚠️ {len(blockers)} blocked session(s) found![/red]\n")
            table = Table(box=box.ROUNDED)
            table.add_column("Blocker SID")
            table.add_column("Blocker User")
            table.add_column("Blocked SID")
            table.add_column("Wait Time (s)")
            table.add_column("Wait Event")
            for row in blockers:
                table.add_row(str(row[0]), row[1], str(row[2]), str(row[4]), row[5])
            console.print(table)
        
        # ============================================================
        # Section 6: Wait Events
        # ============================================================
        console.print("\n" + "="*60)
        console.print("[bold cyan]⏳ SECTION 6: TOP WAIT EVENTS[/bold cyan]")
        console.print("="*60 + "\n")
        
        table = Table(box=box.ROUNDED)
        table.add_column("Wait Event", style="cyan")
        table.add_column("Wait Class")
        table.add_column("Total Waits", justify="right")
        table.add_column("Time Waited (s)", justify="right")
        
        cursor.execute("""
            SELECT event, wait_class, total_waits, 
                   ROUND(time_waited/100, 2) as time_waited_secs
            FROM v$system_event
            WHERE wait_class != 'Idle'
            ORDER BY time_waited DESC
            FETCH FIRST 10 ROWS ONLY
        """)
        
        for row in cursor:
            table.add_row(row[0][:50], row[1], f"{row[2]:,}", f"{row[3]:,.2f}")
        console.print(table)
        
        # ============================================================
        # Summary
        # ============================================================
        console.print("\n" + "="*60)
        console.print("[bold green]✅ REPORT COMPLETE[/bold green]")
        console.print("="*60)
        console.print(f"\n[dim]All queries were READ-ONLY (SELECT only)[/dim]")
        console.print(f"[dim]Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
        
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
    finally:
        cursor.close()
        conn.close()
        tunnel.stop()
        console.print("[dim]Connection closed[/dim]")


if __name__ == "__main__":
    run_report()
