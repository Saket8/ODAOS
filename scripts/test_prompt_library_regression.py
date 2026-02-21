import asyncio
import os
import sys
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.services.prompt_service import PromptService
from src.api.services.chat_service import ChatService

async def run_regression():
    print("Initializing Services...")
    prompt_service = PromptService()
    chat_service = ChatService()
    await chat_service.initialize()
    
    # Get all prompts (assuming there are 35, let's fetch a large page)
    response = await prompt_service.list_prompts(page=1, per_page=100)
    prompts = response.prompts
    
    print(f"\nFound {len(prompts)} prompts in the library.")
    print("-" * 50)
    
    success_count = 0
    fail_count = 0
    
    for prompt_summary in prompts:
        prompt_id = prompt_summary.id
        title = prompt_summary.title
        category = prompt_summary.category
        
        # We need the full prompt to get the template and default values
        prompt = await prompt_service.get_prompt(prompt_id)
        if not prompt:
            print(f"❌ [FAIL] {title} - Could not load full prompt")
            fail_count += 1
            continue
            
        print(f"\n▶ Testing [{category}] {title}")
        
        # Build query
        try:
            query = prompt.prompt_template
            for key, val in prompt.default_values.items():
                query = query.replace(f"{{{key}}}", str(val))
            print(f"  Query: {query[:100]}...")
        except Exception as e:
            print(f"❌ [FAIL] Template resolution error: {e}")
            fail_count += 1
            continue
            
        # Execute
        try:
            has_text = False
            has_chart = False
            error = None
            
            # Using prompt_category explicitly to enforce routing
            stream = chat_service.stream_prompt_response(
                message=query,
                session_id=f"test-regress-{prompt_id}",
                execution_id=prompt_id,
                prompt_category=category
            )
            
            async for event in stream:
                if isinstance(event, dict):
                    if event.get("type") == "chart":
                        has_chart = True
                    elif event.get("type") == "error":
                        error = event.get("message")
                elif isinstance(event, str):
                    if "Error executing prompt" in event:
                        error = event
                    elif len(event.strip()) > 0:
                        has_text = True
            
            if error:
                print(f"❌ [FAIL] Execution Error: {error}")
                fail_count += 1
                continue
                
            if not has_text:
                print(f"❌ [FAIL] No text response generated")
                fail_count += 1
                continue
                
            is_analytics = any(val in category.lower() for val in ("analytics", "business", "brm"))
            if is_analytics and not has_chart:
                print(f"❌ [FAIL] Analytics category but NO CHART returned!")
                fail_count += 1
                continue
                
            status_msg = "✅ [PASS] "
            if is_analytics:
                status_msg += "(Charts + Text)"
            else:
                status_msg += "(Text Only)"
                
            print(status_msg)
            success_count += 1
            
        except Exception as e:
            print(f"❌ [FAIL] Exception during execution: {e}")
            fail_count += 1
            
    print("\n" + "=" * 50)
    print(f"Regression Test Complete.")
    print(f"Total: {len(prompts)} | Passed: {success_count} | Failed: {fail_count}")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(run_regression())
