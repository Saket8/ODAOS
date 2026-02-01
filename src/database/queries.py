"""Oracle Database SQL Queries for ODAOS tools.

These queries are used by the MCP servers when connected to an actual Oracle database.
They replace the mock data when database connectivity is established.
"""

# ============================================================================
# Performance Monitoring Queries
# ============================================================================

# Get current database metrics
GET_DATABASE_METRICS = """
SELECT 
    (SELECT VALUE FROM V$SYSSTAT WHERE NAME = 'CPU used by this session') as cpu_value,
    (SELECT BYTES FROM V$SGAINFO WHERE NAME = 'Fixed SGA Size') + 
    (SELECT BYTES FROM V$SGAINFO WHERE NAME = 'Redo Buffers') as sga_used,
    (SELECT VALUE FROM V$PARAMETER WHERE NAME = 'sga_max_size') as sga_max,
    (SELECT COUNT(*) FROM V$SESSION WHERE STATUS = 'ACTIVE' AND TYPE = 'USER') as active_sessions,
    (SELECT COUNT(*) FROM V$SESSION WHERE TYPE = 'USER') as total_sessions,
    (SELECT VALUE FROM V$SYSSTAT WHERE NAME = 'user commits') as user_commits,
    (SELECT VALUE FROM V$SYSSTAT WHERE NAME = 'user rollbacks') as user_rollbacks
FROM DUAL
"""

# Get top SQL by elapsed time
GET_TOP_SQL = """
SELECT * FROM (
    SELECT 
        sql_id,
        sql_text,
        executions,
        ROUND(elapsed_time/1000000, 2) as elapsed_secs,
        ROUND(cpu_time/1000000, 2) as cpu_secs,
        ROUND(buffer_gets/NULLIF(executions,0), 0) as buffer_gets_per_exec,
        ROUND(disk_reads/NULLIF(executions,0), 0) as disk_reads_per_exec,
        ROUND(rows_processed/NULLIF(executions,0), 0) as rows_per_exec,
        plan_hash_value
    FROM V$SQL
    WHERE executions > 0
    ORDER BY elapsed_time DESC
)
WHERE ROWNUM <= :top_n
"""

# Get tablespace usage
GET_TABLESPACE_USAGE = """
SELECT 
    ts.tablespace_name,
    ts.status,
    ROUND(df.total_bytes/1024/1024, 2) as total_mb,
    ROUND(df.total_bytes/1024/1024 - NVL(fs.free_bytes, 0)/1024/1024, 2) as used_mb,
    ROUND(NVL(fs.free_bytes, 0)/1024/1024, 2) as free_mb,
    ROUND((df.total_bytes - NVL(fs.free_bytes, 0))/df.total_bytes * 100, 2) as used_pct,
    df.autoextensible
FROM dba_tablespaces ts
LEFT JOIN (
    SELECT tablespace_name, SUM(bytes) as total_bytes,
           MAX(autoextensible) as autoextensible
    FROM dba_data_files
    GROUP BY tablespace_name
) df ON ts.tablespace_name = df.tablespace_name
LEFT JOIN (
    SELECT tablespace_name, SUM(bytes) as free_bytes
    FROM dba_free_space
    GROUP BY tablespace_name
) fs ON ts.tablespace_name = fs.tablespace_name
WHERE ts.contents = 'PERMANENT'
ORDER BY used_pct DESC
"""

# Get wait events
GET_WAIT_EVENTS = """
SELECT 
    event,
    wait_class,
    total_waits,
    time_waited,
    ROUND(average_wait * 100, 2) as avg_wait_ms
FROM V$SYSTEM_EVENT
WHERE wait_class != 'Idle'
ORDER BY time_waited DESC
FETCH FIRST 10 ROWS ONLY
"""


# ============================================================================
# Self-Healing Queries
# ============================================================================

# Check blocking sessions
GET_BLOCKING_SESSIONS = """
SELECT 
    s1.sid as blocker_sid,
    s1.serial# as blocker_serial,
    s1.username as blocker_username,
    s1.machine as blocker_machine,
    s1.program as blocker_program,
    s1.sql_id as blocker_sql_id,
    s2.sid as blocked_sid,
    s2.serial# as blocked_serial,
    s2.username as blocked_username,
    s2.wait_class,
    s2.event,
    s2.seconds_in_wait,
    o.object_name as locked_object
FROM V$SESSION s1
JOIN V$SESSION s2 ON s1.sid = s2.blocking_session
LEFT JOIN V$LOCKED_OBJECT lo ON s2.sid = lo.session_id
LEFT JOIN DBA_OBJECTS o ON lo.object_id = o.object_id
WHERE s2.blocking_session IS NOT NULL
ORDER BY s2.seconds_in_wait DESC
"""

# Get recent ORA errors from alert log (requires X$DBGALERTEXT or ADR views)
GET_ALERT_LOG_ERRORS = """
SELECT 
    originating_timestamp as error_time,
    message_text as error_message,
    message_type,
    module_id
FROM V$DIAG_ALERT_EXT
WHERE message_text LIKE 'ORA-%'
  AND originating_timestamp > SYSDATE - :hours/24
ORDER BY originating_timestamp DESC
FETCH FIRST 100 ROWS ONLY
"""

# Get tablespace status for healing
GET_TABLESPACE_STATUS_DETAILED = """
SELECT 
    ts.tablespace_name,
    df.file_name,
    ROUND(df.bytes/1024/1024, 2) as size_mb,
    ROUND((df.bytes - NVL(fs.free_bytes, 0))/1024/1024, 2) as used_mb,
    ROUND((df.bytes - NVL(fs.free_bytes, 0))/df.bytes * 100, 2) as used_pct,
    df.autoextensible,
    ROUND(df.maxbytes/1024/1024, 2) as max_mb,
    df.increment_by as next_extend
FROM dba_tablespaces ts
JOIN dba_data_files df ON ts.tablespace_name = df.tablespace_name
LEFT JOIN (
    SELECT tablespace_name, file_id, SUM(bytes) as free_bytes
    FROM dba_free_space
    GROUP BY tablespace_name, file_id
) fs ON df.tablespace_name = fs.tablespace_name AND df.file_id = fs.file_id
WHERE ts.contents = 'PERMANENT'
ORDER BY used_pct DESC
"""


# ============================================================================
# Generate DDL Commands
# ============================================================================

# Extend tablespace DDL template
EXTEND_TABLESPACE_DDL = """
-- Option 1: Add a new datafile
ALTER TABLESPACE {tablespace_name} ADD DATAFILE SIZE {size_mb}M AUTOEXTEND ON NEXT 100M MAXSIZE 32767M;

-- Option 2: Resize existing datafile
-- ALTER DATABASE DATAFILE '{datafile_path}' RESIZE {new_size_mb}M;
"""

# Kill session DDL template
KILL_SESSION_DDL = """ALTER SYSTEM KILL SESSION '{sid},{serial}'{immediate};"""


# ============================================================================
# Cost Optimization Queries (OCI-related, not database)
# ============================================================================

# These would typically use OCI SDK, not database queries
# Included here for reference

OCI_COST_QUERY_DIMENSIONS = [
    "SERVICE",
    "COMPARTMENT_NAME", 
    "TAG",
    "RESOURCE_ID"
]

# Query for database-side resource usage metrics
GET_DB_RESOURCE_USAGE = """
SELECT 
    resource_name,
    current_utilization,
    max_utilization,
    initial_allocation,
    limit_value
FROM V$RESOURCE_LIMIT
WHERE resource_name IN ('sessions', 'processes', 'transactions')
"""

# Get ASM disk usage (if using ASM)
GET_ASM_DISK_USAGE = """
SELECT 
    name as disk_group,
    ROUND(total_mb, 2) as total_mb,
    ROUND(free_mb, 2) as free_mb,
    ROUND((total_mb - free_mb)/total_mb * 100, 2) as used_pct,
    type
FROM V$ASM_DISKGROUP
ORDER BY used_pct DESC
"""
