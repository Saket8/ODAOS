"""ODAOS Command Line Interface.

Interactive CLI for database operations using the Multi-Agent Orchestrator.

Usage:
    python odaos_cli.py
    # or
    python -m odaos_cli
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Set UTF-8 encoding for Windows (needed for terminal charts)
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Enable UTF-8 console output on Windows
    try:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")
    except Exception:
        pass

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
| `/analytics` | Enter analytics mode for visualizations |
| `/clear` | Clear conversation history |
| `/quit` | Exit the CLI |

**Example Queries:**
- "How is my database performing?"
- "Are there any blocking sessions?"
- "What are our top cost categories?"
- "Give me a complete health check"
- "Why is the database slow?"
- "Find idle resources"

**Analytics Mode Queries:**
- "Show me customer distribution by region"
- "What's our product market share?"
- "Display customer acquisition trends"
- "Analyze churn by region"
"""


class ODAOSCLI:
    """Interactive CLI for ODAOS."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.orchestrator = None
        self.analytics_agent = None
        self.conversation_id = f"cli-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.analytics_mode = False
    
    async def initialize(self):
        """Initialize the orchestrator."""
        console.print("\n[dim]Initializing ODAOS components...[/dim]")
        
        from src.orchestrator import ODAOSOrchestrator
        from src.agents.analytics import AnalyticsAgent
        
        self.orchestrator = ODAOSOrchestrator()
        self.orchestrator.new_conversation(self.conversation_id)
        
        # Initialize analytics agent
        self.analytics_agent = AnalyticsAgent()
        
        console.print("[green]Ready![/green]\n")

    
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
        
        elif cmd == "/analytics":
            self.analytics_mode = True
            return """**📊 Analytics Mode Activated!**

**Ask anything in your own words** - the AI understands natural language!

Examples (but feel free to phrase differently):

🥧 **Pie Charts** - Customer regions, product share, service revenue
🔥 **Heatmaps** - Overdue vs ARPU, usage by time, churn risk, complaints
📈 **Scatter Plots** - ARPU vs churn probability
📉 **Line Charts** - Acquisition trends, revenue growth

**Sample ways to ask:**
- "Show me where our customers are located"
- "Which products are selling best?"
- "Who are our high-risk customers?"
- "How has revenue changed over time?"
- "Compare complaints across regions"

The AI interprets your intent - no fixed phrasing required!

Type `/back` to return to normal mode."""
        
        elif cmd == "/back":
            self.analytics_mode = False
            return "Returned to normal mode."
        
        elif cmd == "/clear":
            self.conversation_id = f"cli-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            self.orchestrator.new_conversation(self.conversation_id)
            self.analytics_agent.new_conversation()
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
                
                # Regular query - send to appropriate agent
                if self.analytics_mode:
                    response = await self.analytics_agent.chat(user_input)
                    title = "[bold magenta]Analytics[/bold magenta]"
                    border = "magenta"
                else:
                    response = await self.chat(user_input)
                    title = "[bold green]ODAOS[/bold green]"
                    border = "green"
                
                console.print(Panel(
                    Markdown(response),
                    title=title,
                    border_style=border
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
