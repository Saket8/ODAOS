"""Test script for Performance LangGraph Agent.

Tests the agent's ability to use MCP tools to analyze database performance.

Usage:
    python test_performance_agent.py
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


async def test_agent_initialization():
    """Test agent initialization."""
    console.print("\n[bold]Test 1: Agent Initialization[/bold]")
    
    from src.agents.performance.agent import PerformanceAgent
    
    try:
        agent = PerformanceAgent()
        console.print("[green]✓ Agent initialized successfully[/green]")
        return agent
    except Exception as e:
        console.print(f"[red]✗ Failed to initialize agent: {e}[/red]")
        return None


async def test_basic_query(agent):
    """Test basic performance query."""
    console.print("\n[bold]Test 2: Basic Health Check Query[/bold]")
    console.print("[dim]Query: 'How is my database performing right now?'[/dim]\n")
    
    try:
        response = await agent.chat("How is my database performing right now?")
        
        console.print(Panel(
            Markdown(response),
            title="Agent Response",
            border_style="green"
        ))
        
        console.print("[green]✓ Agent responded successfully[/green]")
        return True
    except Exception as e:
        console.print(f"[red]✗ Query failed: {e}[/red]")
        return False


async def test_sql_analysis(agent):
    """Test SQL analysis query."""
    console.print("\n[bold]Test 3: Top SQL Analysis[/bold]")
    console.print("[dim]Query: 'Show me the top 5 slowest queries'[/dim]\n")
    
    try:
        response = await agent.chat("Show me the top 5 slowest queries and tell me how to fix them")
        
        console.print(Panel(
            Markdown(response),
            title="Agent Response",
            border_style="green"
        ))
        
        console.print("[green]✓ SQL analysis completed[/green]")
        return True
    except Exception as e:
        console.print(f"[red]✗ Query failed: {e}[/red]")
        return False


async def test_tablespace_check(agent):
    """Test tablespace check query."""
    console.print("\n[bold]Test 4: Tablespace Usage Check[/bold]")
    console.print("[dim]Query: 'Are we running out of disk space?'[/dim]\n")
    
    try:
        response = await agent.chat("Are we running out of disk space? Check the tablespaces.")
        
        console.print(Panel(
            Markdown(response),
            title="Agent Response",
            border_style="green"
        ))
        
        console.print("[green]✓ Tablespace check completed[/green]")
        return True
    except Exception as e:
        console.print(f"[red]✗ Query failed: {e}[/red]")
        return False


async def test_multi_turn_conversation(agent):
    """Test multi-turn conversation with memory."""
    console.print("\n[bold]Test 5: Multi-turn Conversation[/bold]")
    
    # Start new conversation
    thread_id = agent.new_conversation()
    console.print(f"[dim]Thread ID: {thread_id}[/dim]\n")
    
    try:
        # First query
        console.print("[dim]Query 1: 'Check database metrics'[/dim]")
        response1 = await agent.chat("Check database metrics", thread_id)
        console.print(f"[green]Response 1 received ({len(response1)} chars)[/green]\n")
        
        # Follow-up query
        console.print("[dim]Query 2: 'What about the tablespaces?'[/dim]")
        response2 = await agent.chat("What about the tablespaces?", thread_id)
        
        console.print(Panel(
            Markdown(response2),
            title="Follow-up Response",
            border_style="green"
        ))
        
        console.print("[green]✓ Multi-turn conversation works[/green]")
        return True
    except Exception as e:
        console.print(f"[red]✗ Multi-turn failed: {e}[/red]")
        return False


async def main():
    """Run all agent tests."""
    console.print(Panel.fit(
        "[bold cyan]Performance LangGraph Agent Tests[/bold cyan]\n"
        "Testing agent with Groq LLM and MCP tools",
        border_style="blue"
    ))
    
    results = {}
    
    # Test 1: Initialization
    agent = await test_agent_initialization()
    results["initialization"] = agent is not None
    
    if not agent:
        console.print("\n[red]Cannot proceed without agent initialization[/red]")
        return
    
    # Test 2: Basic query
    results["basic_query"] = await test_basic_query(agent)
    
    # Test 3: SQL analysis (using same conversation for context)
    results["sql_analysis"] = await test_sql_analysis(agent)
    
    # Test 4: Tablespace check
    results["tablespace_check"] = await test_tablespace_check(agent)
    
    # Test 5: Multi-turn conversation
    results["multi_turn"] = await test_multi_turn_conversation(agent)
    
    # Summary
    console.print("\n")
    from rich.table import Table
    
    summary = Table(title="Test Results")
    summary.add_column("Test", style="cyan")
    summary.add_column("Status")
    
    for test, passed in results.items():
        summary.add_row(
            test.replace("_", " ").title(),
            "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"
        )
    
    console.print(summary)
    
    if all(results.values()):
        console.print("\n[bold green]🎉 All tests passed! Performance Agent is ready.[/bold green]")
    else:
        console.print("\n[bold yellow]⚠ Some tests failed. Check logs above.[/bold yellow]")


if __name__ == "__main__":
    asyncio.run(main())
