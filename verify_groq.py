"""Verification script to validate Groq API integration.

Run this script to verify that the ODAOS LLM integration is working correctly.

Usage:
    python verify_groq.py
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


async def verify_configuration():
    """Verify configuration is loaded correctly."""
    console.print("\n[bold blue]Step 1: Verifying Configuration[/bold blue]")
    
    try:
        from src.core.config import get_settings
        settings = get_settings()
        
        table = Table(title="Configuration Status")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("LLM Provider", settings.odaos_llm_provider.value)
        table.add_row("Groq Model", settings.groq_model)
        table.add_row("Groq API Key", "✓ Set" if settings.groq_api_key else "✗ Missing")
        table.add_row("OCI Profile", settings.oci_profile)
        table.add_row("OCI Config Path", str(settings.oci_config_path))
        
        console.print(table)
        return True
    except Exception as e:
        console.print(f"[red]Configuration Error: {e}[/red]")
        return False


async def verify_provider_factory():
    """Verify LLM provider factory creates correct instance."""
    console.print("\n[bold blue]Step 2: Verifying Provider Factory[/bold blue]")
    
    try:
        from src.core.providers import get_provider_info
        info = get_provider_info()
        
        table = Table(title="Provider Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Provider", info["provider"])
        table.add_row("Model", info["model"])
        table.add_row("Has Credentials", "✓ Yes" if info["has_credentials"] else "✗ No")
        table.add_row("Ready", "✓ Yes" if info["ready"] else "✗ No")
        
        console.print(table)
        return info["ready"]
    except Exception as e:
        console.print(f"[red]Provider Factory Error: {e}[/red]")
        return False


async def verify_groq_connection():
    """Verify Groq API connectivity with a simple request."""
    console.print("\n[bold blue]Step 3: Testing Groq API Connection[/bold blue]")
    
    try:
        from src.core.providers import create_llm
        from langchain_core.messages import HumanMessage
        
        console.print("Creating LLM instance...", style="dim")
        llm = create_llm()
        
        console.print("Sending test message to Groq...", style="dim")
        response = await llm.ainvoke([
            HumanMessage(content="Respond with exactly: ODAOS_OK")
        ])
        
        console.print(f"Response: [green]{response.content[:100]}[/green]")
        
        if "ODAOS_OK" in response.content or "OK" in response.content.upper():
            console.print("[green]✓ Groq API connection successful![/green]")
            return True
        else:
            console.print("[yellow]⚠ Response received but unexpected format[/yellow]")
            return True  # Still connected
            
    except Exception as e:
        console.print(f"[red]Groq API Error: {e}[/red]")
        return False


async def verify_agent_runtime():
    """Verify the agent runtime can be initialized and respond."""
    console.print("\n[bold blue]Step 4: Testing Agent Runtime[/bold blue]")
    
    try:
        from src.agent import ODAOSAgent
        
        console.print("Initializing ODAOS Agent...", style="dim")
        agent = ODAOSAgent()
        
        console.print("Sending test query to agent...", style="dim")
        response = await agent.chat("What is your name and what can you help with? Be brief.")
        
        console.print(Panel(
            response[:500] + ("..." if len(response) > 500 else ""),
            title="Agent Response",
            border_style="green"
        ))
        
        console.print("[green]✓ Agent runtime working![/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]Agent Runtime Error: {e}[/red]")
        return False


async def verify_oci_config():
    """Verify OCI configuration is accessible."""
    console.print("\n[bold blue]Step 5: Verifying OCI Configuration[/bold blue]")
    
    try:
        from oci.config import from_file
        from src.core.config import get_settings
        
        settings = get_settings()
        
        console.print(f"Loading OCI profile: {settings.oci_profile}", style="dim")
        oci_config = from_file(
            file_location=str(settings.oci_config_path),
            profile_name=settings.oci_profile
        )
        
        table = Table(title="OCI Configuration")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Region", oci_config.get("region", "N/A"))
        table.add_row("Tenancy", oci_config.get("tenancy", "N/A")[:50] + "...")
        table.add_row("User", oci_config.get("user", "N/A")[:50] + "...")
        
        console.print(table)
        console.print("[green]✓ OCI configuration loaded successfully![/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]OCI Config Error: {e}[/red]")
        return False


async def main():
    """Run all verification steps."""
    console.print(Panel.fit(
        "[bold cyan]ODAOS Integration Verification[/bold cyan]\n"
        "Validating Groq API, LangChain, and OCI integration",
        border_style="blue"
    ))
    
    results = {
        "Configuration": await verify_configuration(),
        "Provider Factory": await verify_provider_factory(),
        "Groq API": await verify_groq_connection(),
        "Agent Runtime": await verify_agent_runtime(),
        "OCI Config": await verify_oci_config(),
    }
    
    # Summary
    console.print("\n")
    summary = Table(title="Verification Summary")
    summary.add_column("Component", style="cyan")
    summary.add_column("Status", style="green")
    
    all_passed = True
    for component, passed in results.items():
        status = "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"
        summary.add_row(component, status)
        if not passed:
            all_passed = False
    
    console.print(summary)
    
    if all_passed:
        console.print("\n[bold green]🎉 All verifications passed! ODAOS is ready.[/bold green]")
    else:
        console.print("\n[bold yellow]⚠ Some verifications failed. Check the output above.[/bold yellow]")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
