"""Check revenue data in BRM"""
import asyncio
import sys
sys.path.insert(0, '.')
from src.database.connection import get_connection_manager
from datetime import datetime

async def check_revenue():
    manager = get_connection_manager()
    await manager.initialize()
    
    print('=== BILL_T Totals ===')
    query = """
    SELECT 
        SUM(CURRENT_TOTAL) as total_billed,
        SUM(DUE) as total_due,
        MIN(CREATED_T) as min_date,
        MAX(CREATED_T) as max_date,
        COUNT(*) as bill_count
    FROM PIN.BILL_T
    """
    result = await manager.execute_query(query)
    for r in result:
        min_dt = datetime.fromtimestamp(r['MIN_DATE']) if r['MIN_DATE'] else None
        max_dt = datetime.fromtimestamp(r['MAX_DATE']) if r['MAX_DATE'] else None
        total = r["TOTAL_BILLED"]
        due = r["TOTAL_DUE"]
        cnt = r["BILL_COUNT"]
        print(f'Total Billed: {total}')
        print(f'Total Due: {due}')
        print(f'Bill Count: {cnt}')
        print(f'Date Range: {min_dt} to {max_dt}')
    
    print()
    print('=== Monthly Bill Summary ===')
    query = """
    SELECT 
        TRUNC(CREATED_T / 86400 / 30) as month_bucket,
        COUNT(*) as bill_count,
        SUM(CURRENT_TOTAL) as revenue
    FROM PIN.BILL_T
    GROUP BY TRUNC(CREATED_T / 86400 / 30)
    ORDER BY month_bucket
    """
    result = await manager.execute_query(query)
    for r in result:
        print(f'  Month bucket {r["MONTH_BUCKET"]}: {r["BILL_COUNT"]} bills, Revenue: {r["REVENUE"]}')
    
    print()
    print('=== PRODUCT_T Categories ===')
    query = """
    SELECT NAME, DESCR, POID_TYPE
    FROM PIN.PRODUCT_T
    WHERE ROWNUM <= 10
    """
    result = await manager.execute_query(query)
    for r in result:
        print(f'  {r["NAME"]}: {r["POID_TYPE"]}')

asyncio.run(check_revenue())
