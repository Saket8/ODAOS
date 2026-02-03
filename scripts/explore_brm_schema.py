"""Explore BRM Schema for Analytics Planning"""
import asyncio
import sys
sys.path.insert(0, '.')
from src.database.connection import get_connection_manager

async def explore_core_tables():
    manager = get_connection_manager()
    await manager.initialize()
    
    # Core BRM tables to explore
    core_tables = [
        ('PIN', 'ACCOUNT_T'),
        ('PIN', 'BILLINFO_T'),
        ('PIN', 'ITEM_T'),
        ('PIN', 'EVENT_T'),
        ('PIN', 'SERVICE_T'),
        ('PIN', 'PURCHASED_PRODUCT_T'),
        ('PIN', 'BAL_GRP_T'),
        ('PIN', 'PROFILE_T'),
    ]
    
    for schema, table in core_tables:
        print(f'\n=== {schema}.{table} ===')
        
        # Get column info - embed values directly
        query = f"""
        SELECT column_name, data_type
        FROM all_tab_columns 
        WHERE owner = '{schema}' AND table_name = '{table}'
        ORDER BY column_id
        FETCH FIRST 20 ROWS ONLY
        """
        try:
            result = await manager.execute_query(query)
            for r in result:
                print(f'  {r["COLUMN_NAME"]}: {r["DATA_TYPE"]}')
            
            # Get row count estimate
            count_q = f'SELECT COUNT(*) as cnt FROM {schema}.{table} WHERE ROWNUM <= 100001'
            cnt = await manager.execute_query(count_q)
            row_count = cnt[0]['CNT'] if cnt else 0
            print(f'  ** ROW COUNT: {row_count} **')
        except Exception as e:
            print(f'  Error: {e}')

asyncio.run(explore_core_tables())
