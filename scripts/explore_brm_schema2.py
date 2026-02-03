"""Explore BRM Schema Part 2 - Billing and Revenue Tables"""
import asyncio
import sys
sys.path.insert(0, '.')
from src.database.connection import get_connection_manager

async def explore_billing():
    manager = get_connection_manager()
    await manager.initialize()
    
    # More tables for revenue analysis
    tables = [
        ('PIN', 'EVENT_BILLING_PRODUCT_T'),
        ('PIN', 'BAL_GRP_BALS_T'),
        ('PIN', 'PRODUCT_T'),
        ('PIN', 'BILL_T'),
        ('PIN', 'ACCOUNT_NAMEINFO_T'),
        ('PIN', 'PAYMENT_T'),
        ('ECE', 'RATEDEVENT'),
        ('ECE', 'CUSTOMER'),
    ]
    
    for schema, table in tables:
        print(f'--- {schema}.{table} ---')
        query = f"""
        SELECT column_name, data_type
        FROM all_tab_columns 
        WHERE owner = '{schema}' AND table_name = '{table}'
        ORDER BY column_id
        FETCH FIRST 15 ROWS ONLY
        """
        try:
            result = await manager.execute_query(query)
            for r in result:
                col = r["COLUMN_NAME"]
                dtype = r["DATA_TYPE"]
                print(f'  {col}: {dtype}')
            
            count_q = f'SELECT COUNT(*) as cnt FROM {schema}.{table} WHERE ROWNUM <= 10001'
            cnt = await manager.execute_query(count_q)
            print(f'  ** ROWS: {cnt[0]["CNT"]} **')
        except Exception as e:
            print(f'  Error: {e}')
        print()

asyncio.run(explore_billing())
