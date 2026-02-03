-- =============================================================================
-- ODAOS Read-Only User Setup Script
-- Creates ODAOS_USER with SELECT access to all objects in specified schemas
-- Target Schemas: PIN, PDC, PDC_XREF, BOC_DB, ECE
-- =============================================================================

-- Connect as SYSDBA or a privileged user to run this script
-- Example: sqlplus sys/<password>@<connect_string> as sysdba

-- =============================================================================
-- Step 1: Create the ODAOS_USER
-- =============================================================================

-- Drop user if exists (optional - uncomment if needed)
-- DROP USER ODAOS_USER CASCADE;

CREATE USER ODAOS_USER IDENTIFIED BY "D1devlop_121#"
    DEFAULT TABLESPACE USERS
    TEMPORARY TABLESPACE TEMP
    QUOTA 50M ON USERS;

-- =============================================================================
-- Step 2: Grant basic session privileges
-- =============================================================================

GRANT CREATE SESSION TO ODAOS_USER;

-- =============================================================================
-- Step 3: Grant READ-ONLY access to all objects in target schemas
-- =============================================================================

-- Grant SELECT on all tables in PIN schema
BEGIN
    FOR t IN (SELECT table_name FROM all_tables WHERE owner = 'PIN') LOOP
        EXECUTE IMMEDIATE 'GRANT SELECT ON PIN.' || t.table_name || ' TO ODAOS_USER';
    END LOOP;
END;
/

-- Grant SELECT on all views in PIN schema
BEGIN
    FOR v IN (SELECT view_name FROM all_views WHERE owner = 'PIN') LOOP
        EXECUTE IMMEDIATE 'GRANT SELECT ON PIN.' || v.view_name || ' TO ODAOS_USER';
    END LOOP;
END;
/

-- Grant SELECT on all tables in PDC schema
BEGIN
    FOR t IN (SELECT table_name FROM all_tables WHERE owner = 'PDC') LOOP
        EXECUTE IMMEDIATE 'GRANT SELECT ON PDC.' || t.table_name || ' TO ODAOS_USER';
    END LOOP;
END;
/

-- Grant SELECT on all views in PDC schema
BEGIN
    FOR v IN (SELECT view_name FROM all_views WHERE owner = 'PDC') LOOP
        EXECUTE IMMEDIATE 'GRANT SELECT ON PDC.' || v.view_name || ' TO ODAOS_USER';
    END LOOP;
END;
/

-- Grant SELECT on all tables in PDC_XREF schema
BEGIN
    FOR t IN (SELECT table_name FROM all_tables WHERE owner = 'PDC_XREF') LOOP
        EXECUTE IMMEDIATE 'GRANT SELECT ON PDC_XREF.' || t.table_name || ' TO ODAOS_USER';
    END LOOP;
END;
/

-- Grant SELECT on all views in PDC_XREF schema
BEGIN
    FOR v IN (SELECT view_name FROM all_views WHERE owner = 'PDC_XREF') LOOP
        EXECUTE IMMEDIATE 'GRANT SELECT ON PDC_XREF.' || v.view_name || ' TO ODAOS_USER';
    END LOOP;
END;
/

-- Grant SELECT on all tables in BOC_DB schema
BEGIN
    FOR t IN (SELECT table_name FROM all_tables WHERE owner = 'BOC_DB') LOOP
        EXECUTE IMMEDIATE 'GRANT SELECT ON BOC_DB.' || t.table_name || ' TO ODAOS_USER';
    END LOOP;
END;
/

-- Grant SELECT on all views in BOC_DB schema
BEGIN
    FOR v IN (SELECT view_name FROM all_views WHERE owner = 'BOC_DB') LOOP
        EXECUTE IMMEDIATE 'GRANT SELECT ON BOC_DB.' || v.view_name || ' TO ODAOS_USER';
    END LOOP;
END;
/

-- Grant SELECT on all tables in ECE schema
BEGIN
    FOR t IN (SELECT table_name FROM all_tables WHERE owner = 'ECE') LOOP
        EXECUTE IMMEDIATE 'GRANT SELECT ON ECE.' || t.table_name || ' TO ODAOS_USER';
    END LOOP;
END;
/

-- Grant SELECT on all views in ECE schema
BEGIN
    FOR v IN (SELECT view_name FROM all_views WHERE owner = 'ECE') LOOP
        EXECUTE IMMEDIATE 'GRANT SELECT ON ECE.' || v.view_name || ' TO ODAOS_USER';
    END LOOP;
END;
/

-- =============================================================================
-- Step 4: Grant access to performance views (V$ views) for monitoring
-- =============================================================================

-- Grant SELECT on key V$ views for performance monitoring
GRANT SELECT ON V_$SESSION TO ODAOS_USER;
GRANT SELECT ON V_$SQL TO ODAOS_USER;
GRANT SELECT ON V_$SYSMETRIC TO ODAOS_USER;
GRANT SELECT ON V_$INSTANCE TO ODAOS_USER;
GRANT SELECT ON V_$VERSION TO ODAOS_USER;
GRANT SELECT ON V_$LOCK TO ODAOS_USER;
GRANT SELECT ON V_$LOCKED_OBJECT TO ODAOS_USER;
GRANT SELECT ON V_$SYSTEM_EVENT TO ODAOS_USER;
GRANT SELECT ON V_$SGA TO ODAOS_USER;
GRANT SELECT ON V_$PGA_TARGET_ADVICE TO ODAOS_USER;

-- Grant SELECT on DBA views for tablespace monitoring
GRANT SELECT ON DBA_TABLESPACES TO ODAOS_USER;
GRANT SELECT ON DBA_TABLESPACE_USAGE_METRICS TO ODAOS_USER;
GRANT SELECT ON DBA_DATA_FILES TO ODAOS_USER;
GRANT SELECT ON DBA_FREE_SPACE TO ODAOS_USER;

-- =============================================================================
-- Step 5: Create synonyms for easier access (optional)
-- =============================================================================

-- Create public synonyms or private synonyms if needed
-- This allows ODAOS_USER to query without schema prefix

-- Example: CREATE SYNONYM ODAOS_USER.accounts FOR PIN.ACCOUNT_T;

-- =============================================================================
-- Verification: Check granted privileges
-- =============================================================================

-- Run this to verify grants
SELECT grantee, table_name, privilege
FROM dba_tab_privs
WHERE grantee = 'ODAOS_USER'
ORDER BY table_name;

-- Check system privileges
SELECT privilege
FROM dba_sys_privs
WHERE grantee = 'ODAOS_USER';

COMMIT;

-- =============================================================================
-- Connection Test
-- =============================================================================
-- Test the new user connection:
-- sqlplus ODAOS_USER/D1devlop_121#@localhost:1521/brmpdb1.dbsubnet.devtestvcn.oraclevcn.com
-- SELECT COUNT(*) FROM PIN.ACCOUNT_T;  -- Test read access
