"""Quick test for Cost Optimization Agent - single query only."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

async def main():
    console.print("[bold]Cost Optimization Agent Quick Test[/bold]\n")
    
    from src.agents.cost_optimization.agent import CostOptimizationAgent
    
    console.print("Initializing agent...")
    agent = CostOptimizationAgent()
    console.print("[green]✓ Agent initialized[/green]\n")
    
    console.print("[dim]Query: 'What are our top 3 cost categories?'[/dim]\n")
    console.print("[yellow]Calling Groq API (may take a moment)...[/yellow]")
    
    response = await agent.chat("What are our top 3 cost categories?")
    
    console.print(Panel(
        Markdown(response),
        title="Agent Response",
        border_style="green"
    ))
    
    console.print("\n[bold green]✓ Cost Optimization Agent test passed![/bold green]")

if __name__ == "__main__":
    asyncio.run(main())
