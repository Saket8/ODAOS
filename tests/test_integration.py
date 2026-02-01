"""ODAOS Integration Test Suite.

Comprehensive tests for all MCP servers and agents.

Usage:
    python -m pytest tests/test_integration.py -v
    # or run directly:
    python tests/test_integration.py
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


# ============================================================================
# MCP Server Tests
# ============================================================================

class TestPerformanceMCPServer:
    """Tests for Performance MCP Server."""
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test that all performance tools are registered."""
        from src.mcp_servers.performance.server import list_tools
        tools = await list_tools()
        assert len(tools) == 3
        tool_names = [t.name for t in tools]
        assert "get_database_metrics" in tool_names
        assert "analyze_top_sql" in tool_names
        assert "check_tablespace_usage" in tool_names
    
    @pytest.mark.asyncio
    async def test_get_database_metrics(self):
        """Test database metrics tool."""
        from src.mcp_servers.performance.server import call_tool
        result = await call_tool("get_database_metrics", {})
        data = json.loads(result[0].text)
        assert "cpu" in data
        assert "memory" in data
        assert "sessions" in data
    
    @pytest.mark.asyncio
    async def test_analyze_top_sql(self):
        """Test SQL analysis tool."""
        from src.mcp_servers.performance.server import call_tool
        result = await call_tool("analyze_top_sql", {"top_n": 5})
        data = json.loads(result[0].text)
        assert "sql_statements" in data
        assert len(data["sql_statements"]) <= 5
    
    @pytest.mark.asyncio
    async def test_check_tablespace_usage(self):
        """Test tablespace check tool."""
        from src.mcp_servers.performance.server import call_tool
        result = await call_tool("check_tablespace_usage", {"threshold": 80})
        data = json.loads(result[0].text)
        assert "summary" in data
        assert "alerts" in data or "healthy" in data


class TestSelfHealingMCPServer:
    """Tests for Self-Healing MCP Server."""
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test that all self-healing tools are registered."""
        from src.mcp_servers.self_healing.server import list_tools
        tools = await list_tools()
        assert len(tools) == 5
        tool_names = [t.name for t in tools]
        assert "monitor_alert_log" in tool_names
        assert "check_blocking_sessions" in tool_names
        assert "extend_tablespace" in tool_names
        assert "kill_session" in tool_names
    
    @pytest.mark.asyncio
    async def test_monitor_alert_log(self):
        """Test alert log monitoring tool."""
        from src.mcp_servers.self_healing.server import call_tool
        result = await call_tool("monitor_alert_log", {"hours": 24})
        data = json.loads(result[0].text)
        assert "summary" in data
        assert "errors" in data
    
    @pytest.mark.asyncio
    async def test_check_blocking_sessions(self):
        """Test blocking session detection."""
        from src.mcp_servers.self_healing.server import call_tool
        result = await call_tool("check_blocking_sessions", {})
        data = json.loads(result[0].text)
        assert "summary" in data
        assert "blockers" in data
    
    @pytest.mark.asyncio
    async def test_extend_tablespace_ddl(self):
        """Test DDL generation for tablespace extension."""
        from src.mcp_servers.self_healing.server import call_tool
        result = await call_tool("extend_tablespace", {"tablespace_name": "USERS", "size_mb": 1024})
        data = json.loads(result[0].text)
        assert data["status"] == "PENDING_APPROVAL"
        assert "ddl_scripts" in data
        assert data["approval_required"] == True
    
    @pytest.mark.asyncio
    async def test_kill_session_command(self):
        """Test kill session command generation."""
        from src.mcp_servers.self_healing.server import call_tool
        result = await call_tool("kill_session", {"sid": 123, "serial": 456})
        data = json.loads(result[0].text)
        assert data["status"] == "PENDING_APPROVAL"
        assert "ALTER SYSTEM KILL SESSION" in data["ddl_script"]


class TestCostOptimizationMCPServer:
    """Tests for Cost Optimization MCP Server."""
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test that all cost tools are registered."""
        from src.mcp_servers.cost_optimization.server import list_tools
        tools = await list_tools()
        assert len(tools) == 4
        tool_names = [t.name for t in tools]
        assert "get_oci_costs" in tool_names
        assert "analyze_compute_utilization" in tool_names
        assert "list_idle_resources" in tool_names
        assert "forecast_costs" in tool_names
    
    @pytest.mark.asyncio
    async def test_get_oci_costs(self):
        """Test OCI cost query."""
        from src.mcp_servers.cost_optimization.server import call_tool
        result = await call_tool("get_oci_costs", {"days": 30})
        data = json.loads(result[0].text)
        assert "summary" in data
        assert "total_cost" in data["summary"]
    
    @pytest.mark.asyncio
    async def test_analyze_compute_utilization(self):
        """Test compute utilization analysis."""
        from src.mcp_servers.cost_optimization.server import call_tool
        result = await call_tool("analyze_compute_utilization", {"threshold": 30})
        data = json.loads(result[0].text)
        assert "summary" in data
        assert "underutilized_resources" in data
    
    @pytest.mark.asyncio
    async def test_list_idle_resources(self):
        """Test idle resource detection."""
        from src.mcp_servers.cost_optimization.server import call_tool
        result = await call_tool("list_idle_resources", {})
        data = json.loads(result[0].text)
        assert "summary" in data
        assert "stopped_instances" in data
    
    @pytest.mark.asyncio
    async def test_forecast_costs(self):
        """Test cost forecasting."""
        from src.mcp_servers.cost_optimization.server import call_tool
        result = await call_tool("forecast_costs", {"days_ahead": 30, "budget_amount": 10000})
        data = json.loads(result[0].text)
        assert "forecasts" in data
        assert "budget_analysis" in data


# ============================================================================
# Agent Tests
# ============================================================================

class TestPerformanceAgent:
    """Tests for Performance Agent."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initializes correctly."""
        from src.agents.performance import PerformanceAgent
        agent = PerformanceAgent()
        assert agent is not None
        assert agent.llm is not None
    
    @pytest.mark.asyncio
    async def test_agent_has_tools(self):
        """Test agent has correct tools bound."""
        from src.agents.performance.agent import PERFORMANCE_TOOLS
        assert len(PERFORMANCE_TOOLS) == 3


class TestSelfHealingAgent:
    """Tests for Self-Healing Agent."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initializes correctly."""
        from src.agents.self_healing import SelfHealingAgent
        agent = SelfHealingAgent()
        assert agent is not None
    
    @pytest.mark.asyncio
    async def test_agent_has_tools(self):
        """Test agent has correct tools bound."""
        from src.agents.self_healing.agent import SELF_HEALING_TOOLS
        assert len(SELF_HEALING_TOOLS) == 5


class TestCostOptimizationAgent:
    """Tests for Cost Optimization Agent."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initializes correctly."""
        from src.agents.cost_optimization import CostOptimizationAgent
        agent = CostOptimizationAgent()
        assert agent is not None
    
    @pytest.mark.asyncio
    async def test_agent_has_tools(self):
        """Test agent has correct tools bound."""
        from src.agents.cost_optimization.agent import COST_OPTIMIZATION_TOOLS
        assert len(COST_OPTIMIZATION_TOOLS) == 4


class TestOrchestrator:
    """Tests for Multi-Agent Orchestrator."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator initializes correctly."""
        from src.orchestrator import ODAOSOrchestrator
        orchestrator = ODAOSOrchestrator()
        assert orchestrator is not None
        assert orchestrator.graph is not None
    
    @pytest.mark.asyncio
    async def test_query_classification(self):
        """Test query classification."""
        from src.orchestrator import classify_query, create_llm
        from src.core.providers import create_llm as create
        
        llm = create()
        
        # Test performance query
        result = await classify_query(llm, "Check database metrics")
        assert result.category in ["performance", "composite"]
        
        # Test cost query
        result = await classify_query(llm, "How much are we spending?")
        assert result.category in ["cost", "composite"]


# ============================================================================
# Run Tests Directly
# ============================================================================

async def run_all_tests():
    """Run all integration tests and display results."""
    console.print(Panel.fit(
        "[bold cyan]ODAOS Integration Test Suite[/bold cyan]\n"
        "Testing all MCP servers and agents",
        border_style="blue"
    ))
    
    results = {}
    
    # MCP Server Tests
    console.print("\n[bold]1. Performance MCP Server[/bold]")
    tests = TestPerformanceMCPServer()
    try:
        await tests.test_list_tools()
        await tests.test_get_database_metrics()
        await tests.test_analyze_top_sql()
        await tests.test_check_tablespace_usage()
        results["Performance MCP"] = True
        console.print("[green]✓ All tests passed[/green]")
    except Exception as e:
        results["Performance MCP"] = False
        console.print(f"[red]✗ Failed: {e}[/red]")
    
    console.print("\n[bold]2. Self-Healing MCP Server[/bold]")
    tests = TestSelfHealingMCPServer()
    try:
        await tests.test_list_tools()
        await tests.test_monitor_alert_log()
        await tests.test_check_blocking_sessions()
        await tests.test_extend_tablespace_ddl()
        await tests.test_kill_session_command()
        results["Self-Healing MCP"] = True
        console.print("[green]✓ All tests passed[/green]")
    except Exception as e:
        results["Self-Healing MCP"] = False
        console.print(f"[red]✗ Failed: {e}[/red]")
    
    console.print("\n[bold]3. Cost Optimization MCP Server[/bold]")
    tests = TestCostOptimizationMCPServer()
    try:
        await tests.test_list_tools()
        await tests.test_get_oci_costs()
        await tests.test_analyze_compute_utilization()
        await tests.test_list_idle_resources()
        await tests.test_forecast_costs()
        results["Cost Optimization MCP"] = True
        console.print("[green]✓ All tests passed[/green]")
    except Exception as e:
        results["Cost Optimization MCP"] = False
        console.print(f"[red]✗ Failed: {e}[/red]")
    
    console.print("\n[bold]4. Agent Initialization Tests[/bold]")
    try:
        from src.agents import PerformanceAgent, SelfHealingAgent, CostOptimizationAgent
        PerformanceAgent()
        SelfHealingAgent()
        CostOptimizationAgent()
        results["Agents"] = True
        console.print("[green]✓ All agents initialized[/green]")
    except Exception as e:
        results["Agents"] = False
        console.print(f"[red]✗ Failed: {e}[/red]")
    
    console.print("\n[bold]5. Orchestrator Tests[/bold]")
    try:
        from src.orchestrator import ODAOSOrchestrator
        ODAOSOrchestrator()
        results["Orchestrator"] = True
        console.print("[green]✓ Orchestrator initialized[/green]")
    except Exception as e:
        results["Orchestrator"] = False
        console.print(f"[red]✗ Failed: {e}[/red]")
    
    # Summary
    console.print("\n")
    table = Table(title="Integration Test Results")
    table.add_column("Component", style="cyan")
    table.add_column("Status")
    
    for component, passed in results.items():
        table.add_row(
            component,
            "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"
        )
    
    console.print(table)
    
    passed = sum(results.values())
    total = len(results)
    
    if passed == total:
        console.print(f"\n[bold green]🎉 All {total} integration tests passed![/bold green]")
    else:
        console.print(f"\n[bold yellow]⚠ {passed}/{total} tests passed[/bold yellow]")
    
    return all(results.values())


if __name__ == "__main__":
    asyncio.run(run_all_tests())
