#!/usr/bin/env python
"""Test ODAOS_USER database connection and verify permissions."""

import oracledb
import os

# Initialize thick mode with Instant Client
oracledb.init_oracle_client(lib_dir=r'C:\Users\saura503\OneDrive - KPN BV\software\instantclient_21_20')

# Connection details from .env
user = 'ODAOS_USER'
password = 'D1Devlop_121#A'
dsn = 'localhost:1521/brmsitpdb.dbsubnet.devtestvcn.oraclevcn.com'

print('=' * 60)
print('ODAOS_USER Connection Test Results')
print('=' * 60)

try:
    conn = oracledb.connect(user=user, password=password, dsn=dsn)
    cursor = conn.cursor()
    
    # Test 1: Current user
    cursor.execute('SELECT USER FROM DUAL')
    print(f'[OK] Current User: {cursor.fetchone()[0]}')
    
    # Test 2: Database version
    cursor.execute('SELECT BANNER FROM V$VERSION WHERE ROWNUM = 1')
    print(f'[OK] Database: {cursor.fetchone()[0]}')
    
    # Test 3: Test V$ performance views
    try:
        cursor.execute('SELECT COUNT(*) FROM V$SESSION')
        print(f'[OK] V$SESSION access: {cursor.fetchone()[0]} sessions')
    except Exception as e:
        print(f'[FAIL] V$SESSION access: {e}')
    
    # Test 4: Check accessible schemas
    cursor.execute('''
        SELECT DISTINCT owner 
        FROM all_tables 
        WHERE owner IN ('PIN', 'PDC', 'PDC_XREF', 'BOC_DB', 'ECE')
        ORDER BY owner
    ''')
    schemas = [s[0] for s in cursor.fetchall()]
    print(f'[OK] Accessible Schemas: {schemas}')
    
    # Test 5: Count tables in each schema
    print('\nTable counts per schema:')
    for schema in ['PIN', 'PDC', 'PDC_XREF', 'BOC_DB', 'ECE']:
        cursor.execute(f"SELECT COUNT(*) FROM all_tables WHERE owner = '{schema}'")
        count = cursor.fetchone()[0]
        status = '[OK]' if count > 0 else '[--]'
        print(f'  {status} {schema}: {count} tables accessible')
    
    conn.close()
    print('\n' + '=' * 60)
    print('All tests passed successfully!')
    print('=' * 60)
    
except oracledb.Error as e:
    print(f'[FAIL] Connection failed: {e}')
except Exception as e:
    print(f'[FAIL] Error: {e}')
