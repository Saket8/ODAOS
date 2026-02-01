"""Test script for Performance MCP Server.

Tests the MCP server using direct function calls (not via stdio transport).

Usage:
    python test_performance_mcp.py
"""
import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

console = Console()


async def test_list_tools():
    """Test listing available tools."""
    console.print("\n[bold]Test 1: List Tools[/bold]")
    
    from src.mcp_servers.performance.server import list_tools
    
    tools = await list_tools()
    
    table = Table(title="Performance MCP Server Tools")
    table.add_column("Tool Name", style="cyan")
    table.add_column("Description", style="green")
    
    for tool in tools:
        desc = tool.description[:60] + "..." if len(tool.description) > 60 else tool.description
        table.add_row(tool.name, desc)
    
    console.print(table)
    console.print(f"[green]✓ Found {len(tools)} tools[/green]")
    return len(tools) == 3


async def test_get_database_metrics():
    """Test get_database_metrics tool."""
    console.print("\n[bold]Test 2: get_database_metrics[/bold]")
    
    from src.mcp_servers.performance.server import call_tool
    
    result = await call_tool("get_database_metrics", {})
    
    # Parse the result
    data = json.loads(result[0].text)
    
    if "error" in data:
        console.print(f"[red]✗ Error: {data['error']}[/red]")
        return False
    
    # Display key metrics
    table = Table(title="Database Metrics (Mock Data)")
    table.add_column("Category", style="cyan")
    table.add_column("Metric", style="white")
    table.add_column("Value", style="green")
    
    # CPU
    cpu = data.get("cpu", {})
    table.add_row("CPU", "Host Utilization", f"{cpu.get('host_cpu_utilization', 0)}%")
    table.add_row("CPU", "DB CPU %", f"{cpu.get('db_cpu_percentage', 0)}%")
    
    # Memory
    mem = data.get("memory", {})
    table.add_row("Memory", "Buffer Cache Hit", f"{mem.get('buffer_cache_hit_ratio', 0)}%")
    
    # Sessions
    sessions = data.get("sessions", {})
    table.add_row("Sessions", "Active", str(sessions.get("active_sessions", 0)))
    table.add_row("Sessions", "Total", str(sessions.get("total_sessions", 0)))
    
    console.print(table)
    console.print("[green]✓ Metrics retrieved successfully[/green]")
    return True


async def test_analyze_top_sql():
    """Test analyze_top_sql tool."""
    console.print("\n[bold]Test 3: analyze_top_sql[/bold]")
    
    from src.mcp_servers.performance.server import call_tool
    
    result = await call_tool("analyze_top_sql", {"top_n": 5, "order_by": "elapsed_time"})
    
    data = json.loads(result[0].text)
    
    if "error" in data:
        console.print(f"[red]✗ Error: {data['error']}[/red]")
        return False
    
    sql_list = data.get("sql_statements", [])
    
    table = Table(title="Top 5 SQL by Elapsed Time")
    table.add_column("SQL ID", style="cyan")
    table.add_column("Elapsed (s)", style="yellow", justify="right")
    table.add_column("Executions", style="white", justify="right")
    table.add_column("SQL Text", style="dim", max_width=40)
    
    for sql in sql_list[:5]:
        text = sql.get("sql_text", "")[:40]
        table.add_row(
            sql.get("sql_id", ""),
            f"{sql.get('elapsed_time_secs', 0):.1f}",
            str(sql.get("executions", 0)),
            text + "..." if len(sql.get("sql_text", "")) > 40 else text
        )
    
    console.print(table)
    console.print(f"[green]✓ Retrieved {len(sql_list)} SQL statements[/green]")
    return len(sql_list) > 0


async def test_check_tablespace_usage():
    """Test check_tablespace_usage tool."""
    console.print("\n[bold]Test 4: check_tablespace_usage[/bold]")
    
    from src.mcp_servers.performance.server import call_tool
    
    result = await call_tool("check_tablespace_usage", {"threshold": 85})
    
    data = json.loads(result[0].text)
    
    if "error" in data:
        console.print(f"[red]✗ Error: {data['error']}[/red]")
        return False
    
    summary = data.get("summary", {})
    alerts = data.get("alerts", [])
    
    # Summary
    console.print(Panel(
        f"Total: {summary.get('total_tablespaces', 0)} | "
        f"[red]Critical: {summary.get('critical_count', 0)}[/red] | "
        f"[yellow]Warning: {summary.get('warning_count', 0)}[/yellow] | "
        f"[green]Healthy: {summary.get('healthy_count', 0)}[/green]",
        title="Tablespace Summary"
    ))
    
    # Alerts
    if alerts:
        table = Table(title="Tablespace Alerts")
        table.add_column("Tablespace", style="cyan")
        table.add_column("Used %", justify="right")
        table.add_column("Severity")
        table.add_column("Action", style="dim", max_width=40)
        
        for alert in alerts:
            sev = alert.get("severity", "")
            sev_style = "red" if sev == "CRITICAL" else "yellow"
            table.add_row(
                alert.get("tablespace_name", ""),
                f"{alert.get('used_percent', 0)}%",
                f"[{sev_style}]{sev}[/{sev_style}]",
                alert.get("action", "")[:40]
            )
        
        console.print(table)
    
    console.print("[green]✓ Tablespace check completed[/green]")
    return True


async def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold cyan]Performance MCP Server Tests[/bold cyan]\n"
        "Testing MCP tools with mock data",
        border_style="blue"
    ))
    
    results = {
        "list_tools": await test_list_tools(),
        "get_database_metrics": await test_get_database_metrics(),
        "analyze_top_sql": await test_analyze_top_sql(),
        "check_tablespace_usage": await test_check_tablespace_usage(),
    }
    
    # Summary
    console.print("\n")
    table = Table(title="Test Results")
    table.add_column("Test", style="cyan")
    table.add_column("Status")
    
    for test, passed in results.items():
        table.add_row(
            test,
            "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"
        )
    
    console.print(table)
    
    if all(results.values()):
        console.print("\n[bold green]🎉 All tests passed! Performance MCP Server is ready.[/bold green]")
    else:
        console.print("\n[bold red]⚠ Some tests failed.[/bold red]")


if __name__ == "__main__":
    asyncio.run(main())
