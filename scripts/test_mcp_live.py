#!/usr/bin/env python
"""Quick test of MCP servers with live database connection."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

async def test_performance_server():
    """Test performance MCP server handlers."""
    print("=" * 60)
    print("Testing Performance MCP Server - Live Database")
    print("=" * 60)
    
    from src.mcp_servers.performance.server import (
        get_database_metrics_handler,
        analyze_top_sql_handler,
        check_tablespace_usage_handler
    )
    
    # Test 1: Database Metrics
    print("\n[1] Testing get_database_metrics_handler()...")
    result = await get_database_metrics_handler()
    print(f"    Data Source: {result.get('data_source', 'UNKNOWN')}")
    if 'instance' in result:
        print(f"    Instance: {result['instance'].get('name', 'N/A')}")
        print(f"    Host: {result['instance'].get('host', 'N/A')}")
    if 'sessions' in result:
        print(f"    Active Sessions: {result['sessions'].get('active_sessions', 'N/A')}")
        print(f"    Total Sessions: {result['sessions'].get('total_sessions', 'N/A')}")
    
    # Test 2: Top SQL
    print("\n[2] Testing analyze_top_sql_handler()...")
    result = await analyze_top_sql_handler(top_n=5)
    print(f"    Data Source: {result.get('data_source', 'UNKNOWN')}")
    sql_count = len(result.get('sql_statements', []))
    print(f"    SQL Statements Retrieved: {sql_count}")
    if sql_count > 0:
        top_sql = result['sql_statements'][0]
        print(f"    Top SQL ID: {top_sql.get('sql_id', 'N/A')}")
        print(f"    Executions: {top_sql.get('executions', 'N/A')}")
    
    # Test 3: Tablespace Usage
    print("\n[3] Testing check_tablespace_usage_handler()...")
    result = await check_tablespace_usage_handler()
    print(f"    Data Source: {result.get('data_source', 'UNKNOWN')}")
    if 'summary' in result:
        print(f"    Total Tablespaces: {result['summary'].get('total_tablespaces', 'N/A')}")
        print(f"    Critical: {result['summary'].get('critical_count', 0)}")
        print(f"    Warning: {result['summary'].get('warning_count', 0)}")


async def test_self_healing_server():
    """Test self-healing MCP server handlers."""
    print("\n" + "=" * 60)
    print("Testing Self-Healing MCP Server - Live Database")
    print("=" * 60)
    
    from src.mcp_servers.self_healing.server import (
        check_blocking_sessions_handler,
        get_tablespace_status_handler
    )
    
    # Test 1: Blocking Sessions
    print("\n[1] Testing check_blocking_sessions_handler()...")
    result = await check_blocking_sessions_handler()
    print(f"    Data Source: {result.get('data_source', 'UNKNOWN')}")
    if 'summary' in result:
        print(f"    Blocking Sessions: {result['summary'].get('blocking_sessions', 0)}")
        print(f"    Total Blocked: {result['summary'].get('total_blocked_sessions', 0)}")
    
    # Test 2: Tablespace Status
    print("\n[2] Testing get_tablespace_status_handler()...")
    result = await get_tablespace_status_handler()
    print(f"    Data Source: {result.get('data_source', 'UNKNOWN')}")
    if 'summary' in result:
        print(f"    Total Tablespaces: {result['summary'].get('total_tablespaces', 'N/A')}")
        print(f"    Action Required: {result['summary'].get('immediate_action_required', False)}")


async def main():
    await test_performance_server()
    await test_self_healing_server()
    print("\n" + "=" * 60)
    print("All MCP Server Tests Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
