"""Test script for Cost Optimization MCP Server.

Tests the MCP server tools for OCI cost analysis and optimization.

Usage:
    python test_cost_optimization_mcp.py
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
    
    from src.mcp_servers.cost_optimization.server import list_tools
    
    tools = await list_tools()
    
    table = Table(title="Cost Optimization MCP Server Tools")
    table.add_column("Tool Name", style="cyan")
    table.add_column("Description", style="green", max_width=50)
    
    for tool in tools:
        desc = tool.description[:50] + "..." if len(tool.description) > 50 else tool.description
        table.add_row(tool.name, desc)
    
    console.print(table)
    console.print(f"[green]✓ Found {len(tools)} tools[/green]")
    return len(tools) == 4


async def test_get_oci_costs():
    """Test get_oci_costs tool."""
    console.print("\n[bold]Test 2: get_oci_costs[/bold]")
    
    from src.mcp_servers.cost_optimization.server import call_tool
    
    result = await call_tool("get_oci_costs", {"days": 30, "group_by": "service"})
    data = json.loads(result[0].text)
    
    if "error" in data:
        console.print(f"[red]✗ Error: {data['error']}[/red]")
        return False
    
    summary = data.get("summary", {})
    
    console.print(Panel(
        f"Total: ${summary.get('total_cost', 0):,.2f} | "
        f"Daily Avg: ${summary.get('daily_average', 0):,.2f} | "
        f"Projected: ${summary.get('projected_monthly', 0):,.2f}",
        title="OCI Costs (30 days)"
    ))
    
    console.print("[green]✓ Cost query works[/green]")
    return True


async def test_analyze_compute():
    """Test analyze_compute_utilization tool."""
    console.print("\n[bold]Test 3: analyze_compute_utilization[/bold]")
    
    from src.mcp_servers.cost_optimization.server import call_tool
    
    result = await call_tool("analyze_compute_utilization", {"threshold": 30})
    data = json.loads(result[0].text)
    
    if "error" in data:
        console.print(f"[red]✗ Error: {data['error']}[/red]")
        return False
    
    summary = data.get("summary", {})
    
    console.print(Panel(
        f"Resources: {summary.get('total_resources', 0)} | "
        f"Underutilized: {summary.get('underutilized_count', 0)} | "
        f"[green]Savings: ${summary.get('potential_monthly_savings', 0):,.2f}/mo[/green]",
        title="Compute Utilization"
    ))
    
    console.print("[green]✓ Compute analysis works[/green]")
    return True


async def test_list_idle_resources():
    """Test list_idle_resources tool."""
    console.print("\n[bold]Test 4: list_idle_resources[/bold]")
    
    from src.mcp_servers.cost_optimization.server import call_tool
    
    result = await call_tool("list_idle_resources", {})
    data = json.loads(result[0].text)
    
    if "error" in data:
        console.print(f"[red]✗ Error: {data['error']}[/red]")
        return False
    
    summary = data.get("summary", {})
    
    console.print(Panel(
        f"Stopped Instances: {summary.get('stopped_instances', 0)} | "
        f"Unattached Volumes: {summary.get('unattached_volumes', 0)} | "
        f"[yellow]Idle Cost: ${summary.get('total_idle_monthly_cost', 0):,.2f}/mo[/yellow]",
        title="Idle Resources"
    ))
    
    console.print("[green]✓ Idle resource detection works[/green]")
    return True


async def test_forecast_costs():
    """Test forecast_costs tool."""
    console.print("\n[bold]Test 5: forecast_costs[/bold]")
    
    from src.mcp_servers.cost_optimization.server import call_tool
    
    result = await call_tool("forecast_costs", {"days_ahead": 30, "budget_amount": 9000})
    data = json.loads(result[0].text)
    
    if "error" in data:
        console.print(f"[red]✗ Error: {data['error']}[/red]")
        return False
    
    forecast = data.get("forecasts", [{}])[0]
    budget = data.get("budget_analysis", {})
    
    status_color = "green" if budget.get("status") == "ON_TRACK" else "red"
    
    console.print(Panel(
        f"30-Day Forecast: ${forecast.get('projected_cost', 0):,.2f} | "
        f"Budget Status: [{status_color}]{budget.get('status', 'N/A')}[/{status_color}] | "
        f"Variance: ${budget.get('variance', 0):,.2f}",
        title="Cost Forecast"
    ))
    
    console.print("[green]✓ Cost forecasting works[/green]")
    return True


async def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold cyan]Cost Optimization MCP Server Tests[/bold cyan]\n"
        "Testing OCI cost analysis and optimization tools",
        border_style="blue"
    ))
    
    results = {
        "list_tools": await test_list_tools(),
        "get_oci_costs": await test_get_oci_costs(),
        "analyze_compute": await test_analyze_compute(),
        "list_idle_resources": await test_list_idle_resources(),
        "forecast_costs": await test_forecast_costs(),
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
        console.print("\n[bold green]🎉 All tests passed! Cost Optimization MCP Server is ready.[/bold green]")
    else:
        console.print("\n[bold red]⚠ Some tests failed.[/bold red]")


if __name__ == "__main__":
    asyncio.run(main())
