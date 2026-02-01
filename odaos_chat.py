"""ODAOS Interactive Chat CLI.

Natural language interface for Oracle database operations.
Uses Groq LLM to interpret questions and query the live database.

Usage:
    python odaos_chat.py
"""
import warnings
warnings.filterwarnings("ignore")

import sys
import os
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

# Initialize Oracle thick mode FIRST
import oracledb
try:
    oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_21_20")
except:
    pass

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Prompt
from rich.live import Live
from datetime import datetime
import json

from src.database.live_queries import LiveDBQueries
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

console = Console()

# Banner
BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║     🔮 ODAOS - Oracle Database AI Operations System           ║
║     ═══════════════════════════════════════════════           ║
║     Interactive Chat with Natural Language Support            ║
╚═══════════════════════════════════════════════════════════════╝
"""

SYSTEM_PROMPT = """You are ODAOS, an expert Oracle Database AI assistant connected to a live Oracle 19c database.
You have access to real-time database metrics and can answer questions about:
- Performance (CPU, memory, sessions, wait events)
- Tablespace usage and space issues
- Top SQL statements and query optimization
- Blocking sessions and locks
- Overall database health

When the user asks a question, analyze the provided data and give:
1. A clear, concise answer
2. Any relevant numbers or metrics
3. Actionable recommendations if issues are found

Be conversational but professional. Format responses in markdown when helpful.
If asked to take action (like kill a session), explain what WOULD be done but note that you're in read-only mode.
"""


class ODAOSChat:
    """Interactive chat interface for ODAOS."""
    
    def __init__(self):
        self.db: LiveDBQueries = None
        self.llm: ChatGroq = None
        self.context_cache = {}
        self.conversation_history = []
    
    def connect(self):
        """Establish database and LLM connections."""
        console.print("[dim]Connecting to database...[/dim]")
        self.db = LiveDBQueries()
        self.db.connect()
        console.print("[green]✓ Connected to database[/green]")
        
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            self.llm = ChatGroq(
                api_key=groq_key,
                model="llama-3.3-70b-versatile",
                temperature=0.3
            )
            console.print("[green]✓ AI Engine ready (Groq LLM)[/green]")
        else:
            console.print("[yellow]⚠ GROQ_API_KEY not found - AI analysis disabled[/yellow]")
    
    def close(self):
        """Close connections."""
        if self.db:
            self.db.close()
    
    def get_context(self) -> str:
        """Get current database context for LLM."""
        # Get basic metrics
        info = self.db.get_database_info()
        metrics = self.db.get_performance_metrics()
        health = self.db.calculate_health_score()
        ts = self.db.get_tablespace_usage()
        blocking = self.db.get_blocking_sessions()
        
        context = f"""
CURRENT DATABASE STATE:
=======================
Database: {info['database']['NAME']} / {info['database']['PDB']}
Version: {info['database']['VERSION'][:50] if info['database']['VERSION'] else 'N/A'}
Uptime: {info['instance']['UPTIME_HOURS']} hours
Status: {info['instance']['STATUS']}

HEALTH SCORE: {health['score']}/100 (Grade {health['grade']})
Issues: {', '.join(health['issues']) if health['issues'] else 'None'}

SESSIONS:
- Active: {metrics['sessions']['ACTIVE']}
- Total: {metrics['sessions']['TOTAL']}
- Blocked: {blocking['blocked_count']}

MEMORY:
- Total SGA: {metrics['sga'].get('Total SGA Size', 0)} MB
- Buffer Cache: {metrics['sga'].get('Buffer Cache Size', 0)} MB
- Shared Pool: {metrics['sga'].get('Shared Pool Size', 0)} MB

TABLESPACES:
- Critical: {ts['summary']['critical']}
- Warning: {ts['summary']['warning']}
- Healthy: {ts['summary']['healthy']}

TOP WAIT EVENTS:
{json.dumps(metrics['wait_events'][:3], indent=2) if metrics['wait_events'] else 'None'}
"""
        return context
    
    def process_command(self, cmd: str) -> str:
        """Process CLI commands."""
        cmd = cmd.lower().strip()
        
        if cmd in ["/help", "/h", "/?", "help"]:
            return """
## Available Commands

| Command | Description |
|---------|-------------|
| `/status` | Show database status and health |
| `/sessions` | Show session information |
| `/tablespaces` | Show tablespace usage |
| `/topsql` | Show top SQL by elapsed time |
| `/blocking` | Check for blocking sessions |
| `/health` | Run health check |
| `/clear` | Clear conversation |
| `/quit` | Exit |

**Or just ask a question in natural language!**
Examples:
- "How is my database performing?"
- "Are there any space issues?"
- "Show me the slowest queries"
- "What should I focus on today?"
"""
        
        elif cmd == "/status":
            info = self.db.get_database_info()
            health = self.db.calculate_health_score()
            return f"""
## Database Status

| Property | Value |
|----------|-------|
| Database | {info['database']['NAME']} |
| Container | {info['database']['PDB']} |
| Open Mode | {info['database']['OPEN_MODE']} |
| Role | {info['database']['DATABASE_ROLE']} |
| Host | {info['instance']['HOST_NAME']} |
| Uptime | {info['instance']['UPTIME_HOURS']} hours |
| **Health Score** | **{health['score']}/100 (Grade {health['grade']})** |
"""
        
        elif cmd == "/sessions":
            metrics = self.db.get_performance_metrics()
            blocking = self.db.get_blocking_sessions()
            return f"""
## Session Information

| Metric | Value |
|--------|-------|
| Active Sessions | {metrics['sessions']['ACTIVE']} |
| Inactive Sessions | {metrics['sessions']['INACTIVE']} |
| Total Sessions | {metrics['sessions']['TOTAL']} |
| **Blocked Sessions** | **{blocking['blocked_count']}** |
| Blockers | {blocking['blocker_count']} |
"""
        
        elif cmd == "/tablespaces":
            ts = self.db.get_tablespace_usage()
            lines = ["## Tablespace Usage\n"]
            lines.append("| Tablespace | Used % | Used MB | Total MB | Status |")
            lines.append("|------------|--------|---------|----------|--------|")
            
            for alert in ts['alerts']:
                lines.append(f"| {alert['name']} | **{alert['used_pct']}%** | {alert['used_mb']:,} | {alert['total_mb']:,} | ⚠️ {alert['severity']} |")
            
            for h in ts['healthy'][:5]:
                lines.append(f"| {h['name']} | {h['used_pct']}% | {h['used_mb']:,} | {h['total_mb']:,} | ✅ OK |")
            
            return "\n".join(lines)
        
        elif cmd == "/topsql":
            sql = self.db.get_top_sql(10)
            lines = ["## Top SQL by Elapsed Time\n"]
            lines.append("| SQL ID | Elapsed (s) | Execs | Gets/Exec | Preview |")
            lines.append("|--------|-------------|-------|-----------|---------|")
            
            for s in sql[:10]:
                preview = (s.get('SQL_PREVIEW') or '')[:40]
                lines.append(f"| `{s['SQL_ID']}` | {s['ELAPSED_SECS']} | {s['EXECUTIONS']:,} | {s['GETS_PER_EXEC'] or 0:,} | {preview}... |")
            
            return "\n".join(lines)
        
        elif cmd == "/blocking":
            blocking = self.db.get_blocking_sessions()
            if blocking['blocked_count'] == 0:
                return "## ✅ No Blocking Sessions\n\nDatabase is running smoothly with no blocked sessions."
            
            lines = [f"## ⚠️ {blocking['blocked_count']} Blocked Sessions\n"]
            lines.append("### Blockers:")
            for b in blocking['blockers']:
                lines.append(f"- SID {b['SID']} ({b['USERNAME']}) blocking {b['VICTIMS']} sessions")
            
            return "\n".join(lines)
        
        elif cmd == "/health":
            health = self.db.calculate_health_score()
            emoji = "✅" if health['grade'] in ["A", "B"] else "⚠️" if health['grade'] == "C" else "🔴"
            
            lines = [f"## {emoji} Health Score: {health['score']}/100 (Grade {health['grade']})\n"]
            
            if health['issues']:
                lines.append("### Issues Found:")
                for issue in health['issues']:
                    lines.append(f"- {issue}")
            else:
                lines.append("No issues detected. Database is healthy!")
            
            return "\n".join(lines)
        
        elif cmd == "/clear":
            self.conversation_history = []
            return "Conversation cleared."
        
        return None  # Not a command
    
    def ask(self, question: str) -> str:
        """Ask a natural language question."""
        if not self.llm:
            return "AI analysis unavailable - GROQ_API_KEY not configured."
        
        # Get fresh context
        context = self.get_context()
        
        # Add to conversation
        self.conversation_history.append({"role": "user", "content": question})
        
        # Build messages
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Current database state:\n{context}\n\nUser question: {question}")
        ]
        
        try:
            response = self.llm.invoke(messages)
            answer = response.content
            self.conversation_history.append({"role": "assistant", "content": answer})
            return answer
        except Exception as e:
            return f"Error getting AI response: {str(e)[:100]}"
    
    def run(self):
        """Run the interactive chat."""
        console.print(Panel(BANNER, border_style="cyan"))
        
        try:
            self.connect()
        except Exception as e:
            console.print(f"[red]Connection failed: {e}[/red]")
            return
        
        console.print("\n[dim]Type your question, a /command, or /help. Type /quit to exit.[/dim]\n")
        
        try:
            while True:
                try:
                    user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
                    
                    if not user_input.strip():
                        continue
                    
                    if user_input.lower().strip() in ["/quit", "/exit", "/q", "exit", "quit"]:
                        console.print("\n[cyan]Goodbye! 👋[/cyan]")
                        break
                    
                    # Check for commands
                    if user_input.startswith("/"):
                        result = self.process_command(user_input)
                        if result:
                            console.print(Panel(Markdown(result), title="[bold green]ODAOS[/bold green]", border_style="green"))
                            continue
                    
                    # Natural language query
                    with console.status("[bold blue]Thinking...", spinner="dots"):
                        response = self.ask(user_input)
                    
                    console.print(Panel(Markdown(response), title="[bold green]ODAOS[/bold green]", border_style="green"))
                    console.print()
                    
                except KeyboardInterrupt:
                    console.print("\n[cyan]Goodbye! 👋[/cyan]")
                    break
                    
        finally:
            self.close()


def main():
    """Main entry point."""
    chat = ODAOSChat()
    chat.run()


if __name__ == "__main__":
    main()
