"""Test script for ODAOS Multi-Agent Orchestrator."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

async def main():
    console.print("[bold cyan]ODAOS Multi-Agent Orchestrator Test[/bold cyan]\n")
    
    from src.orchestrator import ODAOSOrchestrator
    
    console.print("Initializing orchestrator (this loads all 3 agents lazily)...")
    orchestrator = ODAOSOrchestrator()
    console.print("[green]✓ Orchestrator initialized[/green]\n")
    
    # Test 1: General query
    console.print("[bold]Test 1: General Query[/bold]")
    console.print("[dim]Query: 'Hello, what can you do?'[/dim]")
    
    response = await orchestrator.chat("Hello, what can you do?")
    console.print(Panel(
        Markdown(response),
        title="Orchestrator Response",
        border_style="green"
    ))
    
    console.print("\n[bold green]✓ Orchestrator test passed![/bold green]")
    console.print("\n[dim]The orchestrator can route queries to specialized agents:[/dim]")
    console.print("- Performance Agent: database metrics, SQL analysis")
    console.print("- Self-Healing Agent: errors, blocking, remediation")
    console.print("- Cost Agent: OCI costs, optimization")

if __name__ == "__main__":
    asyncio.run(main())
