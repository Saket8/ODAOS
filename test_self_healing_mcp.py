"""Test script for Self-Healing MCP Server.

Tests the MCP server tools for incident detection and remediation.

Usage:
    python test_self_healing_mcp.py
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


async def test_list_tools():
    """Test listing available tools."""
    console.print("\n[bold]Test 1: List Tools[/bold]")
    
    from src.mcp_servers.self_healing.server import list_tools
    
    tools = await list_tools()
    
    table = Table(title="Self-Healing MCP Server Tools")
    table.add_column("Tool Name", style="cyan")
    table.add_column("Description", style="green", max_width=50)
    
    for tool in tools:
        desc = tool.description[:50] + "..." if len(tool.description) > 50 else tool.description
        table.add_row(tool.name, desc)
    
    console.print(table)
    console.print(f"[green]✓ Found {len(tools)} tools[/green]")
    return len(tools) == 5


async def test_monitor_alert_log():
    """Test monitor_alert_log tool."""
    console.print("\n[bold]Test 2: monitor_alert_log[/bold]")
    
    from src.mcp_servers.self_healing.server import call_tool
    
    result = await call_tool("monitor_alert_log", {"hours": 24})
    data = json.loads(result[0].text)
    
    if "error" in data:
        console.print(f"[red]✗ Error: {data['error']}[/red]")
        return False
    
    summary = data.get("summary", {})
    errors = data.get("errors", [])
    
    console.print(Panel(
        f"Total: {summary.get('total_errors', 0)} | "
        f"[red]Critical: {summary.get('critical_count', 0)}[/red] | "
        f"[yellow]Warning: {summary.get('warning_count', 0)}[/yellow]",
        title="Alert Log Summary (24h)"
    ))
    
    if errors:
        table = Table(title="Recent Errors")
        table.add_column("Error", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Severity")
        
        for err in errors[:3]:
            sev = err.get("severity", "")
            sev_style = "red" if sev == "CRITICAL" else "yellow"
            table.add_row(
                err.get("error_code", ""),
                str(err.get("occurrences", 0)),
                f"[{sev_style}]{sev}[/{sev_style}]",
            )
        console.print(table)
    
    console.print("[green]✓ Alert log monitoring works[/green]")
    return True


async def test_check_blocking_sessions():
    """Test check_blocking_sessions tool."""
    console.print("\n[bold]Test 3: check_blocking_sessions[/bold]")
    
    from src.mcp_servers.self_healing.server import call_tool
    
    result = await call_tool("check_blocking_sessions", {})
    data = json.loads(result[0].text)
    
    if "error" in data:
        console.print(f"[red]✗ Error: {data['error']}[/red]")
        return False
    
    summary = data.get("summary", {})
    blockers = data.get("blockers", [])
    
    console.print(Panel(
        f"Blocking Sessions: {summary.get('blocking_sessions', 0)} | "
        f"Total Blocked: {summary.get('total_blocked_sessions', 0)} | "
        f"Longest Wait: {summary.get('longest_wait_secs', 0)}s",
        title="Blocking Session Summary"
    ))
    
    if blockers:
        table = Table(title="Blockers")
        table.add_column("SID", style="cyan")
        table.add_column("User", style="white")
        table.add_column("Blocking", justify="right")
        table.add_column("Risk")
        
        for b in blockers[:3]:
            risk = b.get("risk_level", "")
            risk_style = "red" if risk == "HIGH" else "yellow" if risk == "MEDIUM" else "green"
            table.add_row(
                str(b.get("blocker_sid", "")),
                b.get("blocker_username", ""),
                str(len(b.get("blocked_sessions", []))),
                f"[{risk_style}]{risk}[/{risk_style}]",
            )
        console.print(table)
    
    console.print("[green]✓ Blocking session check works[/green]")
    return True


async def test_get_tablespace_status():
    """Test get_tablespace_status tool."""
    console.print("\n[bold]Test 4: get_tablespace_status[/bold]")
    
    from src.mcp_servers.self_healing.server import call_tool
    
    result = await call_tool("get_tablespace_status", {})
    data = json.loads(result[0].text)
    
    if "error" in data:
        console.print(f"[red]✗ Error: {data['error']}[/red]")
        return False
    
    summary = data.get("summary", {})
    
    console.print(Panel(
        f"Total: {summary.get('total_tablespaces', 0)} | "
        f"[red]Critical: {summary.get('critical_count', 0)}[/red] | "
        f"[yellow]Warning: {summary.get('warning_count', 0)}[/yellow]",
        title="Tablespace Status"
    ))
    
    console.print("[green]✓ Tablespace status check works[/green]")
    return True


async def test_extend_tablespace():
    """Test extend_tablespace tool."""
    console.print("\n[bold]Test 5: extend_tablespace (DDL Generation)[/bold]")
    
    from src.mcp_servers.self_healing.server import call_tool
    
    result = await call_tool("extend_tablespace", {"tablespace_name": "USERS", "size_mb": 2048})
    data = json.loads(result[0].text)
    
    if "error" in data:
        console.print(f"[red]✗ Error: {data['error']}[/red]")
        return False
    
    console.print(f"Action: {data.get('action')} | Status: [yellow]{data.get('status')}[/yellow]")
    console.print(f"Approval Required: {data.get('approval_required')}")
    
    if data.get("ddl_scripts"):
        console.print(Panel(
            data.get("ddl_scripts")[0][:100] + "...",
            title="Generated DDL (truncated)",
            border_style="yellow"
        ))
    
    console.print("[green]✓ DDL generation works[/green]")
    return True


async def test_kill_session():
    """Test kill_session tool."""
    console.print("\n[bold]Test 6: kill_session (Command Generation)[/bold]")
    
    from src.mcp_servers.self_healing.server import call_tool
    
    result = await call_tool("kill_session", {"sid": 145, "serial": 34521, "immediate": True})
    data = json.loads(result[0].text)
    
    if "error" in data:
        console.print(f"[red]✗ Error: {data['error']}[/red]")
        return False
    
    console.print(f"Action: {data.get('action')} | Status: [yellow]{data.get('status')}[/yellow]")
    console.print(f"DDL: [cyan]{data.get('ddl_script')}[/cyan]")
    console.print(f"Approval Required: {data.get('approval_required')}")
    
    console.print("[green]✓ Kill session command generation works[/green]")
    return True


async def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold cyan]Self-Healing MCP Server Tests[/bold cyan]\n"
        "Testing incident detection and remediation tools",
        border_style="blue"
    ))
    
    results = {
        "list_tools": await test_list_tools(),
        "monitor_alert_log": await test_monitor_alert_log(),
        "check_blocking_sessions": await test_check_blocking_sessions(),
        "get_tablespace_status": await test_get_tablespace_status(),
        "extend_tablespace": await test_extend_tablespace(),
        "kill_session": await test_kill_session(),
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
        console.print("\n[bold green]🎉 All tests passed! Self-Healing MCP Server is ready.[/bold green]")
    else:
        console.print("\n[bold red]⚠ Some tests failed.[/bold red]")


if __name__ == "__main__":
    asyncio.run(main())
