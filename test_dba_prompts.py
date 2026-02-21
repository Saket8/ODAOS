import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.orchestrator import ODAOSOrchestrator, classify_query

async def test_classification():
    print("Initializing Orchestrator...")
    orchestrator = ODAOSOrchestrator()
    
    test_prompts = [
        # Performance Prompts (6)
        ("performance", "Show me Active Session History (ASH) for the last 30 minutes"),
        ("performance", "What are my I/O hotspots and datafiles with highest latency?"),
        ("performance", "Show me any non-default instance parameters"),
        ("performance", "What is the database uptime and when did it start?"),
        ("performance", "What are my largest database segments consuming the most space?"),
        ("performance", "Check TEMP tablespace usage and see who is consuming it"),
        
        # Healing Prompts (5)
        ("healing", "Are there any long running sessions exceeding 60 minutes?"),
        ("healing", "What system privileges and roles does user APP_USER have?"),
        ("healing", "Check recent RMAN backup status for failures"),
        ("healing", "How fast is my archive log generating daily in GB?"),
        ("healing", "Check Flash Recovery Area (FRA) space utilization"),
    ]
    
    success_count = 0
    
    print("\nStarting Classification Tests...\n" + "-"*50)
    for expected_cat, prompt in test_prompts:
        result = await classify_query(orchestrator.llm, prompt)
        cat = result.category
        agents = result.agents_needed
        
        if expected_cat == cat and expected_cat in agents:
            status = "PASS"
            success_count += 1
        else:
            status = f"FAIL (Got: {cat}, Expected: {expected_cat})"
            
        print(f"[{status}] Prompt: '{prompt}'")
        print(f"    -> Category: {cat}")
        print(f"    -> Agents Needed: {agents}")
        print(f"    -> Reasoning: {result.reasoning}\n")
        
    print(f"Score: {success_count}/{len(test_prompts)}")

if __name__ == "__main__":
    asyncio.run(test_classification())
