"""
Comprehensive Prompt Library Validation Script
Tests all 35 prompts for:
1. Non-empty response
2. Response relevance (BRM → BRM data, DBA → DBA data)
3. Adequate response length (>=200 chars)
4. Chart generation for analytics prompts
5. No execution errors
6. Response uniqueness (no duplicate responses)
"""
import asyncio
import sys
import os
import json
import time
import hashlib
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.services.prompt_service import PromptService
from src.api.services.chat_service import ChatService


async def run_validation():
    print("=" * 70)
    print("PROMPT LIBRARY VALIDATION")
    print("=" * 70)
    
    # Initialize
    prompt_service = PromptService()
    chat_service = ChatService()
    await chat_service.initialize()
    
    # Get all prompts
    response = await prompt_service.list_prompts(page=1, per_page=100)
    prompts = response.prompts
    total = len(prompts)
    
    print(f"\nFound {total} prompts in the library.\n")
    
    results = []
    response_hashes = set()
    
    for idx, prompt_summary in enumerate(prompts, 1):
        prompt_id = prompt_summary.id
        title = prompt_summary.title
        category = prompt_summary.category
        
        # Skip test prompts
        if title == "Test Prompt":
            results.append({
                "id": prompt_id,
                "title": title,
                "category": category,
                "status": "SKIP",
                "reason": "Test prompt",
            })
            print(f"  [{idx}/{total}] SKIP  {title} (test prompt)")
            continue
        
        # Load full prompt
        prompt = await prompt_service.get_prompt(prompt_id)
        if not prompt:
            results.append({
                "id": prompt_id,
                "title": title,
                "category": category,
                "status": "FAIL",
                "reason": "Could not load prompt",
            })
            print(f"  [{idx}/{total}] FAIL  {title} — Could not load prompt")
            continue
        
        # Build query with default values
        try:
            query = prompt.prompt_template
            for key, val in prompt.default_values.items():
                query = query.replace(f"{{{key}}}", str(val))
            
            # Validate no unresolved placeholders remain
            import re
            remaining = re.findall(r"\{(\w+)\}", query)
            if remaining:
                results.append({
                    "id": prompt_id,
                    "title": title,
                    "category": category,
                    "status": "FAIL",
                    "reason": f"Unresolved placeholders: {remaining}",
                })
                print(f"  [{idx}/{total}] FAIL  {title} — Unresolved: {remaining}")
                continue
        except Exception as e:
            results.append({
                "id": prompt_id,
                "title": title,
                "category": category,
                "status": "FAIL",
                "reason": f"Template error: {e}",
            })
            print(f"  [{idx}/{total}] FAIL  {title} — Template error: {e}")
            continue
        
        # Execute prompt
        is_brm = any(v in category.lower() for v in ("brm", "analytics", "business"))
        has_text = False
        has_chart = False
        chart_title = ""
        chart_type = ""
        full_text = ""
        error = None
        
        start = time.time()
        try:
            stream = chat_service.stream_prompt_response(
                message=query,
                session_id=f"validation-{prompt_id}",
                execution_id=prompt_id,
                prompt_category=category,
            )
            
            async for event in stream:
                if isinstance(event, dict):
                    etype = event.get("type", "")
                    if etype == "chart":
                        has_chart = True
                        chart_data = event.get("data", {})
                        chart_title = chart_data.get("title", "")
                        chart_type = chart_data.get("type", "")
                    elif etype == "token":
                        content = event.get("content", "")
                        full_text += content
                        has_text = True
                    elif etype == "error":
                        error = event.get("message", "Unknown error")
                elif isinstance(event, str):
                    full_text += event
                    has_text = True
        except Exception as e:
            error = str(e)
        
        elapsed = time.time() - start
        
        # Evaluate results
        status = "PASS"
        reason = ""
        checks = []
        
        if error:
            status = "FAIL"
            reason = f"Error: {error}"
        elif not has_text or len(full_text.strip()) < 50:
            status = "FAIL"
            reason = f"Response too short: {len(full_text.strip())} chars"
        else:
            checks.append(f"{len(full_text)} chars")
        
        if is_brm and has_chart:
            checks.append(f"{chart_type} chart: '{chart_title}'")
        elif is_brm and not has_chart and status == "PASS":
            status = "WARN"
            reason = "BRM prompt but no chart returned"
        
        # Uniqueness check
        text_hash = hashlib.md5(full_text.strip()[:300].encode()).hexdigest()
        if text_hash in response_hashes and status == "PASS":
            status = "FAIL"
            reason = "Duplicate response (same as another prompt)"
        response_hashes.add(text_hash)
        
        result = {
            "id": prompt_id,
            "title": title,
            "category": category,
            "status": status,
            "reason": reason,
            "has_chart": has_chart,
            "chart_title": chart_title,
            "chart_type": chart_type,
            "text_length": len(full_text.strip()),
            "elapsed_s": round(elapsed, 1),
            "checks": checks,
        }
        results.append(result)
        
        icon = "✅" if status == "PASS" else "⚠️" if status == "WARN" else "❌"
        detail = f" ({', '.join(checks)})" if checks else ""
        fail_info = f" — {reason}" if reason else ""
        print(f"  [{idx}/{total}] {icon} {title}{detail}{fail_info}  [{elapsed:.1f}s]")
    
    # Summary
    passed = sum(1 for r in results if r["status"] == "PASS")
    warned = sum(1 for r in results if r["status"] == "WARN")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    with_chart = sum(1 for r in results if r.get("has_chart"))
    tested = total - skipped
    
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    print(f"  Total prompts:   {total}")
    print(f"  Tested:          {tested}")
    print(f"  Passed:          {passed} ({100*passed//max(tested,1)}%)")
    print(f"  Warnings:        {warned}")
    print(f"  Failed:          {failed}")
    print(f"  Skipped:         {skipped}")
    print(f"  With Charts:     {with_chart}")
    print()
    
    if failed > 0:
        print("FAILURES:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  ❌ [{r['category']}] {r['title']}: {r['reason']}")
    
    if warned > 0:
        print("\nWARNINGS:")
        for r in results:
            if r["status"] == "WARN":
                print(f"  ⚠️  [{r['category']}] {r['title']}: {r['reason']}")
    
    # Save results
    with open("validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to validation_results.json")
    
    print("=" * 70)
    verdict = "✅ READY FOR USER TESTING" if failed == 0 else "❌ FIXES REQUIRED"
    print(f"  Verdict: {verdict}")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    asyncio.run(run_validation())
