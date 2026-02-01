"""Quick test for Self-Healing Agent - single query only."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

async def main():
    console.print("[bold]Self-Healing Agent Quick Test[/bold]\n")
    
    from src.agents.self_healing.agent import SelfHealingAgent
    
    console.print("Initializing agent...")
    agent = SelfHealingAgent()
    console.print("[green]✓ Agent initialized[/green]\n")
    
    console.print("[dim]Query: 'Check for blocking sessions in the database'[/dim]\n")
    console.print("[yellow]Calling Groq API (may take a moment)...[/yellow]")
    
    response = await agent.chat("Check for blocking sessions in the database")
    
    console.print(Panel(
        Markdown(response),
        title="Agent Response",
        border_style="green"
    ))
    
    console.print("\n[bold green]✓ Self-Healing Agent test passed![/bold green]")

if __name__ == "__main__":
    asyncio.run(main())
