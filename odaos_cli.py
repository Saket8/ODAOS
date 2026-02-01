"""ODAOS Command Line Interface.

Interactive CLI for database operations using the Multi-Agent Orchestrator.

Usage:
    python odaos_cli.py
    # or
    python -m odaos_cli
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

console = Console()

# ASCII Art Banner
BANNER = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║     ██████╗ ██████╗  █████╗  ██████╗ ███████╗                    ║
║    ██╔═══██╗██╔══██╗██╔══██╗██╔═══██╗██╔════╝                    ║
║    ██║   ██║██║  ██║███████║██║   ██║███████╗                    ║
║    ██║   ██║██║  ██║██╔══██║██║   ██║╚════██║                    ║
║    ╚██████╔╝██████╔╝██║  ██║╚██████╔╝███████║                    ║
║     ╚═════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝                    ║
║                                                                   ║
║    Oracle Database AI Operations System                          ║
║    v1.0.0 - Phase 1 MVP                                          ║
╚═══════════════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
**Available Commands:**

| Command | Description |
|---------|-------------|
| `/help` | Show this help message |
| `/health` | Run comprehensive health check |
| `/performance` | Check database performance |
| `/incidents` | Check for incidents and blocking sessions |
| `/costs` | Get OCI cost summary |
| `/forecast` | Get cost forecast |
| `/clear` | Clear conversation history |
| `/quit` | Exit the CLI |

**Example Queries:**
- "How is my database performing?"
- "Are there any blocking sessions?"
- "What are our top cost categories?"
- "Give me a complete health check"
- "Why is the database slow?"
- "Find idle resources"
"""


class ODAOSCLI:
    """Interactive CLI for ODAOS."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.orchestrator = None
        self.conversation_id = f"cli-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    async def initialize(self):
        """Initialize the orchestrator."""
        console.print("\n[dim]Initializing ODAOS components...[/dim]")
        
        from src.orchestrator import ODAOSOrchestrator
        self.orchestrator = ODAOSOrchestrator()
        self.orchestrator.new_conversation(self.conversation_id)
        
        console.print("[green]✓ Ready![/green]\n")
    
    async def process_command(self, user_input: str) -> str:
        """Process special commands."""
        cmd = user_input.lower().strip()
        
        if cmd == "/help":
            return HELP_TEXT
        
        elif cmd == "/health":
            return await self.orchestrator.chat(
                "Perform a comprehensive database health check covering "
                "performance metrics, incidents, and cost optimization."
            )
        
        elif cmd == "/performance":
            return await self.orchestrator.chat("Check current database performance metrics")
        
        elif cmd == "/incidents":
            return await self.orchestrator.chat(
                "Check for any database incidents, errors in alert log, and blocking sessions"
            )
        
        elif cmd == "/costs":
            return await self.orchestrator.chat("What are our current OCI costs by service?")
        
        elif cmd == "/forecast":
            return await self.orchestrator.chat("Forecast our OCI costs for the next 30 days")
        
        elif cmd == "/clear":
            self.conversation_id = f"cli-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            self.orchestrator.new_conversation(self.conversation_id)
            return "Conversation history cleared. Starting fresh!"
        
        elif cmd in ["/quit", "/exit", "/q"]:
            return None
        
        return False  # Not a command
    
    async def chat(self, message: str) -> str:
        """Send a message to the orchestrator with loading indicator."""
        with console.status("[bold blue]Thinking...", spinner="dots"):
            response = await self.orchestrator.chat(message)
        return response
    
    async def run(self):
        """Run the interactive CLI loop."""
        console.print(Panel(
            BANNER,
            border_style="cyan",
            padding=(0, 0)
        ))
        
        await self.initialize()
        
        console.print("[dim]Type your question or /help for commands. /quit to exit.[/dim]\n")
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
                
                if not user_input.strip():
                    continue
                
                # Check for commands
                if user_input.startswith("/"):
                    result = await self.process_command(user_input)
                    
                    if result is None:  # Quit command
                        console.print("\n[bold cyan]Goodbye! 👋[/bold cyan]")
                        break
                    
                    if result is not False:  # Valid command
                        console.print(Panel(
                            Markdown(result),
                            title="[bold green]ODAOS[/bold green]",
                            border_style="green"
                        ))
                        continue
                
                # Regular query - send to orchestrator
                response = await self.chat(user_input)
                
                console.print(Panel(
                    Markdown(response),
                    title="[bold green]ODAOS[/bold green]",
                    border_style="green"
                ))
                console.print()
                
            except KeyboardInterrupt:
                console.print("\n[bold cyan]Goodbye! 👋[/bold cyan]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")


async def main():
    """Main entry point."""
    cli = ODAOSCLI()
    await cli.run()


if __name__ == "__main__":
    asyncio.run(main())
