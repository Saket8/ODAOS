"""Sample queries for analytics planning"""
import asyncio
import sys
sys.path.insert(0, '.')
from src.database.connection import get_connection_manager

async def sample_data():
    manager = get_connection_manager()
    await manager.initialize()
    
    print("=== EVENT_T Date Range ===")
    query = """
    SELECT 
        MIN(CREATED_T) as min_created,
        MAX(CREATED_T) as max_created,
        COUNT(*) as total_events
    FROM PIN.EVENT_T
    """
    result = await manager.execute_query(query)
    print(result)
    
    print("\n=== ITEM_T Types and Amounts ===")
    query = """
    SELECT 
        POID_TYPE, 
        COUNT(*) as cnt
    FROM PIN.ITEM_T
    GROUP BY POID_TYPE
    ORDER BY cnt DESC
    FETCH FIRST 10 ROWS ONLY
    """
    result = await manager.execute_query(query)
    for r in result:
        print(f"  {r['POID_TYPE']}: {r['CNT']}")
    
    print("\n=== ACCOUNT_T Types ===")
    query = """
    SELECT 
        ACCOUNT_TYPE, 
        COUNT(*) as cnt
    FROM PIN.ACCOUNT_T
    GROUP BY ACCOUNT_TYPE
    """
    result = await manager.execute_query(query)
    for r in result:
        print(f"  Type {r['ACCOUNT_TYPE']}: {r['CNT']}")
    
    print("\n=== BILL_T Sample ===")
    query = """
    SELECT * FROM PIN.BILL_T 
    WHERE ROWNUM <= 3
    """
    result = await manager.execute_query(query)
    if result:
        print(f"  Columns: {list(result[0].keys())}")
    
    print("\n=== SERVICE_T Types ===")
    query = """
    SELECT 
        POID_TYPE, 
        COUNT(*) as cnt
    FROM PIN.SERVICE_T
    GROUP BY POID_TYPE
    """
    result = await manager.execute_query(query)
    for r in result:
        print(f"  {r['POID_TYPE']}: {r['CNT']}")
    
    print("\n=== ACCOUNT_NAMEINFO_T Regions ===")
    query = """
    SELECT 
        COUNTRY, 
        CITY,
        COUNT(*) as cnt
    FROM PIN.ACCOUNT_NAMEINFO_T
    GROUP BY COUNTRY, CITY
    ORDER BY cnt DESC
    FETCH FIRST 10 ROWS ONLY
    """
    result = await manager.execute_query(query)
    for r in result:
        print(f"  {r['COUNTRY']}/{r['CITY']}: {r['CNT']}")

asyncio.run(sample_data())
