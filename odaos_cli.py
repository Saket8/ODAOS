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
import logging

# ============================================================================
# Silence Noisy Logs
# ============================================================================
# Suppress INFO logs from external libraries and internal modules for a cleaner CLI
logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("oci").setLevel(logging.WARNING)
logging.getLogger("src.database.connection").setLevel(logging.WARNING)
logging.getLogger("src.orchestrator").setLevel(logging.WARNING)
logging.getLogger("src.agents").setLevel(logging.WARNING)
logging.getLogger("langchain").setLevel(logging.WARNING)
logging.getLogger("langgraph").setLevel(logging.WARNING)

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
        """Initialize the orchestrator and display connection status."""
        console.print("\n[dim]Initializing ODAOS components...[/dim]")
        
        from src.orchestrator import ODAOSOrchestrator
        from src.agents.analytics import AnalyticsAgent
        from src.database.connection import get_connection_manager
        
        # Initialize orchestrator
        self.orchestrator = ODAOSOrchestrator()
        self.orchestrator.new_conversation(self.conversation_id)
        
        # Initialize analytics agent
        self.analytics_agent = AnalyticsAgent()
        
        # Get database connection info for formatted display
        manager = get_connection_manager()
        try:
            db_status = await manager.test_connection()
            if db_status.get("connected"):
                info = db_status["database_info"]
                conn_text = Text()
                conn_text.append("✅ Connected to Oracle Database\n", style="bold green")
                conn_text.append(f"• Instance: ", style="dim")
                conn_text.append(f"{info.get('INSTANCE_NAME', 'Unknown')}\n", style="cyan")
                conn_text.append(f"• Host:     ", style="dim")
                conn_text.append(f"{info.get('HOST_NAME', 'Unknown')}\n", style="cyan")
                conn_text.append(f"• Version:  ", style="dim")
                conn_text.append(f"{info.get('VERSION', 'Unknown').splitlines()[0]}", style="cyan")
                
                console.print(Panel(conn_text, title="[bold blue]Connection Status[/bold blue]", border_style="blue", expand=False))
            else:
                console.print(Panel(f"[red]❌ Database Connection Failed[/red]\n[dim]{db_status.get('error')}[/dim]", title="Error", border_style="red"))
        except Exception as e:
            console.print(f"[red]Error checking database connection: {e}[/red]")
            
        console.print("[green]System Ready![/green]\n")

    
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

**Ask anything in natural language** - the AI interprets your intent!

---

## 🎯 CUSTOMER INSIGHTS

**Geographic Distribution** (Pie/Bar Chart)
- "Show customer distribution by region"
- "Which countries have the most customers?"
- "Create a pie chart of customers by country"

**Product Adoption** (Pie/Bar Chart)
- "What's our product market share?"
- "Which products are selling best?"
- "Show subscription breakdown by product"

---

## 💰 REVENUE ANALYSIS

**Revenue Composition** (Pie/Bar Chart)
- "How is our revenue distributed by service type?"
- "Which services generate the most revenue?"

**Revenue Trends** (Line Chart)
- "Show monthly revenue growth"
- "How has revenue changed over time?"

**Customer Acquisition** (Line Chart)
- "Show customer acquisition trends"
- "How many new customers each month?"

---

## ⚠️ RISK MANAGEMENT

**High-Value At-Risk Customers** (Scatter Plot)
- "Plot ARPU vs churn probability"
- "Who are our high-value customers at risk?"

**Payment Risk** (Heatmap)
- "Create a heatmap of overdue balance vs ARPU"
- "Who are our high-risk non-payment customers?"

**Churn by Region** (Heatmap)
- "Visualize churn risk by region"
- "Where are we losing the most customers?"

---

## 📈 OPERATIONAL INTELLIGENCE

**Service Usage Patterns** (Heatmap)
- "Show usage intensity by time of day"
- "When are our peak usage hours?"

**Complaints & Errors** (Heatmap)
- "Compare complaints vs billing errors by region"
- "Which regions have the most adjustments?"

---

**💡 Tips:** Say "as a pie chart" or "as a bar chart" to change style.

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
                
                # Smart rendering: Use Markdown for results with code blocks (charts).
                # Otherwise, print as raw text to prevent mangling ASCII art/special chars.
                renderable = Markdown(response) if "```" in response else response
                
                console.print(Panel(
                    renderable,
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
