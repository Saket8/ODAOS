"""Quick test for Performance Agent - single query only."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

async def main():
    console.print("[bold]Performance Agent Quick Test[/bold]\n")
    
    from src.agents.performance.agent import PerformanceAgent
    
    console.print("Initializing agent...")
    agent = PerformanceAgent()
    console.print("[green]✓ Agent initialized[/green]\n")
    
    console.print("[dim]Query: 'Check database metrics and give me a brief summary'[/dim]\n")
    console.print("[yellow]Calling Groq API (may take a moment)...[/yellow]")
    
    response = await agent.chat("Check database metrics and give me a brief summary")
    
    console.print(Panel(
        Markdown(response),
        title="Agent Response",
        border_style="green"
    ))
    
    console.print("\n[bold green]✓ Performance Agent test passed![/bold green]")

if __name__ == "__main__":
    asyncio.run(main())
