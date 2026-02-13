
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import get_connection_manager

async def test_analytics_data():
    manager = get_connection_manager()
    await manager.initialize()
    
    queries = {
        "churn_risk": """
        SELECT 
            NVL(ni.COUNTRY, 'Unknown') as label,
            COUNT(*) as total,
            SUM(CASE WHEN (SYSDATE - TO_DATE('1970-01-01','YYYY-MM-DD') - a.MOD_T/86400) > 60 THEN 1 ELSE 0 END) as at_risk
        FROM PIN.ACCOUNT_T a
        LEFT JOIN PIN.ACCOUNT_NAMEINFO_T ni ON a.POID_ID0 = ni.OBJ_ID0
        WHERE a.POID_ID0 > 1
        GROUP BY ni.COUNTRY
        ORDER BY COUNT(*) DESC
        FETCH FIRST 8 ROWS ONLY
        """,
        "arpu_churn": """
        SELECT 
            a.POID_ID0 as account_id,
            NVL(SUM(i.DUE), 0) as x,
            ABS(SYSDATE - TO_DATE('1970-01-01','YYYY-MM-DD') - a.MOD_T/86400) / 180 as y
        FROM PIN.ACCOUNT_T a
        LEFT JOIN PIN.ITEM_T i ON a.POID_ID0 = i.ACCOUNT_OBJ_ID0
        WHERE a.POID_ID0 > 1
        GROUP BY a.POID_ID0, a.MOD_T
        FETCH FIRST 10 ROWS ONLY
        """,
        "db_waits": "SELECT event as label, time_waited as value FROM V$SYSTEM_EVENT WHERE wait_class != 'Idle' FETCH FIRST 5 ROWS ONLY",
        "db_sql": "SELECT sql_text as label, cpu_time as value FROM V$SQL WHERE executions > 0 FETCH FIRST 5 ROWS ONLY",
        "db_storage": "SELECT tablespace_name as label, SUM(bytes)/1024/1024 as value FROM dba_data_files GROUP BY tablespace_name"
    }
    
    for name, sql in queries.items():
        print(f"\n--- Testing {name} ---")
        try:
            result = await manager.execute_query(sql)
            print(f"Result count: {len(result)}")
            if result:
                print(f"First row keys: {list(result[0].keys())}")
                print(f"First row data: {result[0]}")
            else:
                print("No rows returned.")
        except Exception as e:
            print(f"Query failed: {e}")
            
    await manager.close()

if __name__ == "__main__":
    asyncio.run(test_analytics_data())
