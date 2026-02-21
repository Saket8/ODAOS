"""Performance Intelligence MCP Server.

Provides database performance analysis tools for the ODAOS Performance Agent.
Tools include database metrics collection, SQL analysis, and tablespace monitoring.

Usage:
    # Run directly
    python -m src.mcp_servers.performance.server
    
    # Or use as module
    from src.mcp_servers.performance.server import mcp
"""
import logging
from datetime import datetime
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP Server
mcp = Server("odaos-performance")


# ============================================================================
# Tool Input Models
# ============================================================================

class AnalyzeTopSQLInput(BaseModel):
    """Input for analyze_top_sql tool."""
    top_n: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of top SQL statements to analyze"
    )
    order_by: str = Field(
        default="elapsed_time",
        description="Metric to order by: elapsed_time, cpu_time, executions, buffer_gets"
    )


class CheckTablespaceInput(BaseModel):
    """Input for check_tablespace_usage tool."""
    threshold: int = Field(
        default=85,
        ge=0,
        le=100,
        description="Percentage threshold for alerting (default 85%)"
    )


# ============================================================================
# Mock Data (for testing without database connection)
# ============================================================================

def get_mock_database_metrics() -> dict:
    """Return mock database metrics for testing."""
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu": {
            "host_cpu_utilization": 45.2,
            "db_cpu_percentage": 32.5,
            "cpu_count": 4,
        },
        "memory": {
            "sga_target_bytes": 1073741824,  # 1GB
            "pga_target_bytes": 536870912,   # 512MB
            "buffer_cache_hit_ratio": 98.7,
        },
        "sessions": {
            "active_sessions": 12,
            "total_sessions": 45,
            "max_sessions": 300,
            "blocked_sessions": 0,
        },
        "io": {
            "physical_reads_per_sec": 125.3,
            "physical_writes_per_sec": 45.2,
            "redo_writes_per_sec": 89.7,
        },
        "top_wait_events": [
            {"event": "db file sequential read", "wait_time_ms": 1234},
            {"event": "log file sync", "wait_time_ms": 567},
            {"event": "direct path read", "wait_time_ms": 234},
        ],
    }


def get_mock_top_sql(top_n: int = 10, order_by: str = "elapsed_time") -> list:
    """Return mock top SQL for testing."""
    mock_sql = [
        {
            "sql_id": "abc123def",
            "sql_text": "SELECT * FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.status = :1",
            "executions": 15234,
            "elapsed_time_secs": 892.5,
            "cpu_time_secs": 456.2,
            "buffer_gets": 2345678,
            "disk_reads": 12345,
            "parsing_schema": "APP_USER",
            "recommendation": "Consider adding index on orders(status, customer_id)",
        },
        {
            "sql_id": "xyz789ghi",
            "sql_text": "UPDATE inventory SET quantity = quantity - :1 WHERE product_id = :2",
            "executions": 8456,
            "elapsed_time_secs": 567.3,
            "cpu_time_secs": 234.1,
            "buffer_gets": 1234567,
            "disk_reads": 8976,
            "parsing_schema": "APP_USER",
            "recommendation": "High buffer gets - consider query optimization",
        },
        {
            "sql_id": "mno456pqr",
            "sql_text": "SELECT COUNT(*) FROM audit_log WHERE created_at > SYSDATE - 7",
            "executions": 45678,
            "elapsed_time_secs": 345.8,
            "cpu_time_secs": 289.5,
            "buffer_gets": 987654,
            "disk_reads": 5432,
            "parsing_schema": "SYS",
            "recommendation": "Frequent full table scan - consider partitioning by date",
        },
    ]
    
    # Add more mock entries to reach top_n
    for i in range(3, top_n):
        mock_sql.append({
            "sql_id": f"sql{i:03d}abc",
            "sql_text": f"SELECT col1, col2 FROM table_{i} WHERE id = :1",
            "executions": 1000 - (i * 50),
            "elapsed_time_secs": 100.0 - (i * 5),
            "cpu_time_secs": 50.0 - (i * 2),
            "buffer_gets": 100000 - (i * 5000),
            "disk_reads": 1000 - (i * 50),
            "parsing_schema": "APP_USER",
            "recommendation": None,
        })
    
    return mock_sql[:top_n]


def get_mock_tablespace_usage(threshold: int = 85) -> dict:
    """Return mock tablespace usage for testing."""
    tablespaces = [
        {"name": "USERS", "used_mb": 8500, "total_mb": 10000, "used_pct": 85.0, "autoextend": True},
        {"name": "SYSTEM", "used_mb": 950, "total_mb": 1000, "used_pct": 95.0, "autoextend": False},
        {"name": "SYSAUX", "used_mb": 2100, "total_mb": 3000, "used_pct": 70.0, "autoextend": True},
        {"name": "UNDOTBS1", "used_mb": 1800, "total_mb": 2000, "used_pct": 90.0, "autoextend": True},
        {"name": "TEMP", "used_mb": 500, "total_mb": 2000, "used_pct": 25.0, "autoextend": True},
        {"name": "APP_DATA", "used_mb": 45000, "total_mb": 50000, "used_pct": 90.0, "autoextend": True},
        {"name": "APP_INDEX", "used_mb": 12000, "total_mb": 20000, "used_pct": 60.0, "autoextend": True},
    ]
    
    alerts = []
    healthy = []
    
    for ts in tablespaces:
        ts_info = {
            "tablespace_name": ts["name"],
            "used_mb": ts["used_mb"],
            "total_mb": ts["total_mb"],
            "used_percent": ts["used_pct"],
            "free_mb": ts["total_mb"] - ts["used_mb"],
            "autoextend": ts["autoextend"],
        }
        
        if ts["used_pct"] >= 95:
            ts_info["severity"] = "CRITICAL"
            ts_info["action"] = f"Immediately extend tablespace {ts['name']} or add datafile"
            alerts.append(ts_info)
        elif ts["used_pct"] >= threshold:
            ts_info["severity"] = "WARNING"
            ts_info["action"] = f"Plan to extend tablespace {ts['name']} within 48 hours"
            alerts.append(ts_info)
        else:
            ts_info["severity"] = "OK"
            healthy.append(ts_info)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "threshold": threshold,
        "summary": {
            "total_tablespaces": len(tablespaces),
            "critical_count": len([a for a in alerts if a["severity"] == "CRITICAL"]),
            "warning_count": len([a for a in alerts if a["severity"] == "WARNING"]),
            "healthy_count": len(healthy),
        },
        "alerts": sorted(alerts, key=lambda x: x["used_percent"], reverse=True),
        "healthy": healthy,
    }


# ============================================================================
# Tool Handlers
# ============================================================================

@mcp.list_tools()
async def list_tools() -> list[Tool]:
    """List all available performance tools."""
    return [
        Tool(
            name="get_database_metrics",
            description="Get comprehensive Oracle database performance metrics including CPU, memory, sessions, and I/O statistics. Returns current system health snapshot.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="analyze_top_sql",
            description="Analyze the most resource-intensive SQL statements by elapsed time, CPU, or I/O. Returns SQL text, execution statistics, and optimization recommendations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "Number of top SQL statements to return (1-50)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                    "order_by": {
                        "type": "string",
                        "description": "Metric to order by",
                        "enum": ["elapsed_time", "cpu_time", "executions", "buffer_gets"],
                        "default": "elapsed_time",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="check_tablespace_usage",
            description="Check tablespace usage and identify tablespaces exceeding the specified threshold. Returns alerts for tablespaces needing attention.",
            inputSchema={
                "type": "object",
                "properties": {
                    "threshold": {
                        "type": "integer",
                        "description": "Percentage threshold for alerting (0-100)",
                        "default": 85,
                        "minimum": 0,
                        "maximum": 100,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_ash_data",
            description="Get Active Session History (ASH) data including top wait events, top SQL statements consuming database time, and session activity breakdown over a recent time window.",
            inputSchema={
                "type": "object",
                "properties": {
                    "minutes": {
                        "type": "integer",
                        "description": "Number of minutes to look back (default 30)",
                        "default": 30,
                        "minimum": 1,
                        "maximum": 1440,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_io_performance",
            description="Get I/O performance statistics per datafile, including read/write latency and throughput. Identifies I/O hotspots.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_instance_parameters",
            description="Get current Oracle instance parameters. Can show all parameters or only those modified from default.",
            inputSchema={
                "type": "object",
                "properties": {
                    "modified_only": {
                        "type": "boolean",
                        "description": "If true, only show parameters with non-default values",
                        "default": True,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_database_uptime",
            description="Get database uptime, startup time, and general availability status.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_segment_sizes",
            description="Get the largest database segments (tables, indexes, LOBs) to analyze space consumption.",
            inputSchema={
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "Number of segments to return",
                        "default": 20,
                        "minimum": 5,
                        "maximum": 100,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_temp_usage",
            description="Get TEMP tablespace usage and the sessions consuming the most temporary space.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    try:
        if name == "get_database_metrics":
            result = await get_database_metrics_handler()
        elif name == "analyze_top_sql":
            top_n = arguments.get("top_n", 10)
            order_by = arguments.get("order_by", "elapsed_time")
            result = await analyze_top_sql_handler(top_n, order_by)
        elif name == "check_tablespace_usage":
            threshold = arguments.get("threshold", 85)
            result = await check_tablespace_usage_handler(threshold)
        elif name == "get_ash_data":
            minutes = arguments.get("minutes", 30)
            result = await get_ash_data_handler(minutes)
        elif name == "get_io_performance":
            result = await get_io_performance_handler()
        elif name == "get_instance_parameters":
            modified_only = arguments.get("modified_only", True)
            result = await get_instance_parameters_handler(modified_only)
        elif name == "get_database_uptime":
            result = await get_database_uptime_handler()
        elif name == "get_segment_sizes":
            top_n = arguments.get("top_n", 20)
            result = await get_segment_sizes_handler(top_n)
        elif name == "get_temp_usage":
            result = await get_temp_usage_handler()
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        # Format result as JSON string
        import json
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        import json
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e), "tool": name}, indent=2)
        )]


async def get_database_metrics_handler() -> dict:
    """Get database performance metrics.
    
    Queries v$sysmetric, v$session, and related views for current metrics.
    Falls back to mock data if database is not connected.
    """
    try:
        from src.database.connection import get_connection_manager
        
        manager = get_connection_manager()
        
        # Check if we have database credentials configured
        if not manager.dsn or not manager.user:
            logger.info("Database not configured, using mock data")
            return get_mock_database_metrics()
        
        # Initialize connection pool
        await manager.initialize()
        
        session_result = []
        instance_result = []
        sga_result = []
        wait_result = []
        
        # Get session metrics
        try:
            session_query = """
            SELECT 
                COUNT(*) as total_sessions,
                SUM(CASE WHEN status = 'ACTIVE' AND type = 'USER' THEN 1 ELSE 0 END) as active_sessions,
                SUM(CASE WHEN blocking_session IS NOT NULL THEN 1 ELSE 0 END) as blocked_sessions
            FROM V$SESSION
            """
            session_result = await manager.execute_query(session_query)
        except Exception as e:
            logger.warning(f"V$SESSION query failed: {e}")
        
        # Get database version and instance info
        try:
            instance_query = """
            SELECT 
                instance_name,
                host_name,
                version,
                status,
                database_status
            FROM V$INSTANCE
            """
            instance_result = await manager.execute_query(instance_query)
        except Exception as e:
            logger.warning(f"V$INSTANCE query failed: {e}")
        
        # Get SGA info
        try:
            sga_query = """
            SELECT 
                SUM(CASE WHEN name = 'Fixed SGA Size' THEN bytes ELSE 0 END) as fixed_sga,
                SUM(bytes) as total_sga
            FROM V$SGAINFO
            """
            sga_result = await manager.execute_query(sga_query)
        except Exception as e:
            logger.warning(f"V$SGAINFO query failed: {e}")
        
        # Get top wait events
        try:
            wait_query = """
            SELECT event, wait_class, total_waits, time_waited
            FROM V$SYSTEM_EVENT
            WHERE wait_class != 'Idle'
            ORDER BY time_waited DESC
            FETCH FIRST 5 ROWS ONLY
            """
            wait_result = await manager.execute_query(wait_query)
        except Exception as e:
            logger.warning(f"V$SYSTEM_EVENT query failed: {e}")
        
        session_data = session_result[0] if session_result else {}
        instance_data = instance_result[0] if instance_result else {}
        sga_data = sga_result[0] if sga_result else {}
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "data_source": "LIVE",
            "instance": {
                "name": instance_data.get('INSTANCE_NAME', 'Unknown'),
                "host": instance_data.get('HOST_NAME', 'Unknown'),
                "version": instance_data.get('VERSION', 'Unknown'),
                "status": instance_data.get('STATUS', 'Unknown'),
            },
            "sessions": {
                "active_sessions": int(session_data.get('ACTIVE_SESSIONS', 0)),
                "total_sessions": int(session_data.get('TOTAL_SESSIONS', 0)),
                "max_sessions": 1000,  # Default
                "blocked_sessions": int(session_data.get('BLOCKED_SESSIONS', 0)),
            },
            "memory": {
                "sga_total_bytes": int(sga_data.get('TOTAL_SGA', 0)),
            },
            "top_wait_events": [
                {
                    "event": w.get('EVENT', 'Unknown'),
                    "wait_class": w.get('WAIT_CLASS', 'Unknown'),
                    "total_waits": int(w.get('TOTAL_WAITS', 0)),
                    "time_waited": int(w.get('TIME_WAITED', 0)),
                }
                for w in wait_result
            ],
        }
        
        logger.info(f"Retrieved live metrics from {instance_data.get('INSTANCE_NAME', 'database')}")
        return result
        
    except Exception as e:
        logger.warning(f"Database connection failed, using mock data: {e}")
        return get_mock_database_metrics()


async def analyze_top_sql_handler(top_n: int = 10, order_by: str = "elapsed_time") -> dict:
    """Analyze top SQL statements.
    
    Queries v$sql for the most resource-intensive SQL statements.
    Falls back to mock data if database is not connected.
    """
    try:
        from src.database.connection import get_connection_manager
        
        manager = get_connection_manager()
        
        if not manager.dsn or not manager.user:
            logger.info("Database not configured, using mock data")
            return {
                "timestamp": datetime.now().isoformat(),
                "data_source": "MOCK",
                "parameters": {"top_n": top_n, "order_by": order_by},
                "sql_statements": get_mock_top_sql(top_n, order_by),
            }
        
        await manager.initialize()
        
        # Map order_by to column name
        order_column = {
            "elapsed_time": "ELAPSED_TIME",
            "cpu_time": "CPU_TIME", 
            "executions": "EXECUTIONS",
            "buffer_gets": "BUFFER_GETS"
        }.get(order_by, "ELAPSED_TIME")
        
        sql_query = f"""
        SELECT * FROM (
            SELECT 
                sql_id,
                SUBSTR(sql_text, 1, 200) as sql_text,
                executions,
                ROUND(elapsed_time/1000000, 2) as elapsed_secs,
                ROUND(cpu_time/1000000, 2) as cpu_secs,
                buffer_gets,
                disk_reads,
                rows_processed,
                parsing_schema_name,
                plan_hash_value
            FROM V$SQL
            WHERE executions > 0
              AND parsing_schema_name NOT IN ('SYS', 'SYSTEM', 'DBSNMP')
            ORDER BY {order_column} DESC
        )
        WHERE ROWNUM <= :top_n
        """
        
        result = await manager.execute_query(sql_query, {"top_n": top_n})
        
        sql_statements = []
        for row in result:
            sql_statements.append({
                "sql_id": row.get('SQL_ID', 'Unknown'),
                "sql_text": row.get('SQL_TEXT', ''),
                "executions": int(row.get('EXECUTIONS', 0)),
                "elapsed_time_secs": float(row.get('ELAPSED_SECS', 0)),
                "cpu_time_secs": float(row.get('CPU_SECS', 0)),
                "buffer_gets": int(row.get('BUFFER_GETS', 0)),
                "disk_reads": int(row.get('DISK_READS', 0)),
                "rows_processed": int(row.get('ROWS_PROCESSED', 0)),
                "parsing_schema": row.get('PARSING_SCHEMA_NAME', 'Unknown'),
            })
        
        logger.info(f"Retrieved {len(sql_statements)} SQL statements from live database")
        return {
            "timestamp": datetime.now().isoformat(),
            "data_source": "LIVE",
            "parameters": {"top_n": top_n, "order_by": order_by},
            "sql_statements": sql_statements,
        }
        
    except Exception as e:
        logger.warning(f"Database connection failed, using mock data: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "data_source": "MOCK",
            "parameters": {"top_n": top_n, "order_by": order_by},
            "sql_statements": get_mock_top_sql(top_n, order_by),
        }


async def check_tablespace_usage_handler(threshold: int = 85) -> dict:
    """Check tablespace usage against threshold.
    
    Queries dba_tablespace_usage_metrics for tablespace information.
    Falls back to mock data if database is not connected.
    """
    try:
        from src.database.connection import get_connection_manager
        
        manager = get_connection_manager()
        
        if not manager.dsn or not manager.user:
            logger.info("Database not configured, using mock data")
            return get_mock_tablespace_usage(threshold)
        
        await manager.initialize()
        
        ts_query = """
        SELECT 
            ts.tablespace_name,
            ts.status,
            ROUND(df.total_bytes/1024/1024, 2) as total_mb,
            ROUND((df.total_bytes - NVL(fs.free_bytes, 0))/1024/1024, 2) as used_mb,
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
          AND df.total_bytes IS NOT NULL
        ORDER BY used_pct DESC
        """
        
        result = await manager.execute_query(ts_query)
        
        alerts = []
        healthy = []
        
        for row in result:
            used_pct = float(row.get('USED_PCT', 0))
            ts_info = {
                "tablespace_name": row.get('TABLESPACE_NAME', 'Unknown'),
                "status": row.get('STATUS', 'Unknown'),
                "used_mb": float(row.get('USED_MB', 0)),
                "total_mb": float(row.get('TOTAL_MB', 0)),
                "free_mb": float(row.get('FREE_MB', 0)),
                "used_percent": used_pct,
                "autoextend": row.get('AUTOEXTENSIBLE', 'NO') == 'YES',
            }
            
            if used_pct >= 95:
                ts_info["severity"] = "CRITICAL"
                ts_info["action"] = f"Immediately extend tablespace {ts_info['tablespace_name']} or add datafile"
                alerts.append(ts_info)
            elif used_pct >= threshold:
                ts_info["severity"] = "WARNING"
                ts_info["action"] = f"Plan to extend tablespace {ts_info['tablespace_name']} within 48 hours"
                alerts.append(ts_info)
            else:
                ts_info["severity"] = "OK"
                healthy.append(ts_info)
        
        logger.info(f"Retrieved {len(alerts) + len(healthy)} tablespaces from live database")
        return {
            "timestamp": datetime.now().isoformat(),
            "data_source": "LIVE",
            "threshold": threshold,
            "summary": {
                "total_tablespaces": len(alerts) + len(healthy),
                "critical_count": len([a for a in alerts if a["severity"] == "CRITICAL"]),
                "warning_count": len([a for a in alerts if a["severity"] == "WARNING"]),
                "healthy_count": len(healthy),
            },
            "alerts": alerts,
            "healthy": healthy,
        }
        
    except Exception as e:
        logger.warning(f"Database connection failed, using mock data: {e}")
        return get_mock_tablespace_usage(threshold)


# ============================================================================
# New Tool Handlers — Phase 2 (covering all DBA prompts)
# ============================================================================

async def get_ash_data_handler(minutes: int = 30) -> dict:
    """Get Active Session History data.
    
    Queries V$ACTIVE_SESSION_HISTORY for recent session activity,
    top wait events, and SQL consuming the most DB time.
    """
    try:
        from src.database.connection import get_connection_manager
        manager = get_connection_manager()
        
        if not manager.dsn or not manager.user:
            return _mock_ash_data(minutes)
        
        await manager.initialize()
        
        # Top wait events from ASH
        wait_result = []
        try:
            wait_query = """
            SELECT 
                event,
                wait_class,
                COUNT(*) as sample_count,
                COUNT(DISTINCT session_id) as session_count
            FROM V$ACTIVE_SESSION_HISTORY
            WHERE sample_time > SYSDATE - :mins/(24*60)
              AND event IS NOT NULL
            GROUP BY event, wait_class
            ORDER BY COUNT(*) DESC
            FETCH FIRST 10 ROWS ONLY
            """
            wait_result = await manager.execute_query(wait_query.replace(':mins', str(minutes)))
        except Exception as e:
            logger.warning(f"ASH wait events query failed: {e}")
        
        # Top SQL from ASH
        sql_result = []
        try:
            sql_query = """
            SELECT 
                sql_id,
                COUNT(*) as sample_count,
                COUNT(DISTINCT session_id) as session_count,
                ROUND(COUNT(*) * 100 / NULLIF((SELECT COUNT(*) FROM V$ACTIVE_SESSION_HISTORY 
                    WHERE sample_time > SYSDATE - {mins}/(24*60)), 0), 2) as pct_db_time
            FROM V$ACTIVE_SESSION_HISTORY
            WHERE sample_time > SYSDATE - {mins}/(24*60)
              AND sql_id IS NOT NULL
            GROUP BY sql_id
            ORDER BY COUNT(*) DESC
            FETCH FIRST 10 ROWS ONLY
            """.format(mins=minutes)
            sql_result = await manager.execute_query(sql_query)
        except Exception as e:
            logger.warning(f"ASH top SQL query failed: {e}")
        
        # Session activity summary
        activity_result = []
        try:
            activity_query = """
            SELECT 
                session_state,
                COUNT(*) as sample_count
            FROM V$ACTIVE_SESSION_HISTORY
            WHERE sample_time > SYSDATE - {mins}/(24*60)
            GROUP BY session_state
            """.format(mins=minutes)
            activity_result = await manager.execute_query(activity_query)
        except Exception as e:
            logger.warning(f"ASH activity query failed: {e}")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "data_source": "LIVE",
            "analysis_window_minutes": minutes,
            "top_wait_events": [
                {
                    "event": r.get('EVENT', 'Unknown'),
                    "wait_class": r.get('WAIT_CLASS', 'Unknown'),
                    "sample_count": int(r.get('SAMPLE_COUNT', 0)),
                    "session_count": int(r.get('SESSION_COUNT', 0)),
                }
                for r in wait_result
            ],
            "top_sql": [
                {
                    "sql_id": r.get('SQL_ID', 'Unknown'),
                    "sample_count": int(r.get('SAMPLE_COUNT', 0)),
                    "session_count": int(r.get('SESSION_COUNT', 0)),
                    "pct_db_time": float(r.get('PCT_DB_TIME', 0)),
                }
                for r in sql_result
            ],
            "session_activity": {
                r.get('SESSION_STATE', 'Unknown'): int(r.get('SAMPLE_COUNT', 0))
                for r in activity_result
            },
        }
    except Exception as e:
        logger.warning(f"ASH query failed, using mock: {e}")
        return _mock_ash_data(minutes)


def _mock_ash_data(minutes: int = 30) -> dict:
    """Mock ASH data for when DB is not available."""
    return {
        "timestamp": datetime.now().isoformat(),
        "data_source": "MOCK",
        "analysis_window_minutes": minutes,
        "top_wait_events": [
            {"event": "db file sequential read", "wait_class": "User I/O", "sample_count": 245, "session_count": 8},
            {"event": "log file sync", "wait_class": "Commit", "sample_count": 120, "session_count": 15},
            {"event": "buffer busy waits", "wait_class": "Concurrency", "sample_count": 80, "session_count": 5},
        ],
        "top_sql": [
            {"sql_id": "abc123def", "sample_count": 95, "session_count": 3, "pct_db_time": 22.5},
            {"sql_id": "xyz789ghi", "sample_count": 60, "session_count": 2, "pct_db_time": 14.2},
        ],
        "session_activity": {"ON CPU": 350, "WAITING": 480},
    }


async def get_io_performance_handler() -> dict:
    """Get I/O performance statistics per datafile.
    
    Queries V$FILESTAT or V$IOSTAT_FILE for read/write latency and throughput.
    """
    try:
        from src.database.connection import get_connection_manager
        manager = get_connection_manager()
        
        if not manager.dsn or not manager.user:
            return _mock_io_performance()
        
        await manager.initialize()
        
        io_result = []
        try:
            io_query = """
            SELECT 
                df.name as file_name,
                fs.phyrds as physical_reads,
                fs.phywrts as physical_writes,
                fs.readtim as read_time_cs,
                fs.writetim as write_time_cs,
                ROUND(CASE WHEN fs.phyrds > 0 THEN fs.readtim / fs.phyrds * 10 ELSE 0 END, 2) as avg_read_ms,
                ROUND(CASE WHEN fs.phywrts > 0 THEN fs.writetim / fs.phywrts * 10 ELSE 0 END, 2) as avg_write_ms,
                fs.phyblkrd as blocks_read,
                fs.phyblkwrt as blocks_written
            FROM V$FILESTAT fs
            JOIN V$DATAFILE df ON fs.file# = df.file#
            ORDER BY (fs.readtim + fs.writetim) DESC
            FETCH FIRST 15 ROWS ONLY
            """
            io_result = await manager.execute_query(io_query)
        except Exception as e:
            logger.warning(f"V$FILESTAT query failed: {e}")
        
        files = []
        total_reads = 0
        total_writes = 0
        for r in io_result:
            reads = int(r.get('PHYSICAL_READS', 0))
            writes = int(r.get('PHYSICAL_WRITES', 0))
            total_reads += reads
            total_writes += writes
            files.append({
                "file_name": r.get('FILE_NAME', 'Unknown'),
                "physical_reads": reads,
                "physical_writes": writes,
                "avg_read_ms": float(r.get('AVG_READ_MS', 0)),
                "avg_write_ms": float(r.get('AVG_WRITE_MS', 0)),
                "blocks_read": int(r.get('BLOCKS_READ', 0)),
                "blocks_written": int(r.get('BLOCKS_WRITTEN', 0)),
            })
        
        # Identify hotspots
        hotspots = [f for f in files if f["avg_read_ms"] > 10 or f["avg_write_ms"] > 10]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "data_source": "LIVE",
            "summary": {
                "total_files": len(files),
                "total_physical_reads": total_reads,
                "total_physical_writes": total_writes,
                "io_hotspot_count": len(hotspots),
            },
            "files": files,
            "hotspots": hotspots,
        }
    except Exception as e:
        logger.warning(f"I/O performance query failed, using mock: {e}")
        return _mock_io_performance()


def _mock_io_performance() -> dict:
    """Mock I/O performance data."""
    return {
        "timestamp": datetime.now().isoformat(),
        "data_source": "MOCK",
        "summary": {
            "total_files": 5,
            "total_physical_reads": 1250000,
            "total_physical_writes": 340000,
            "io_hotspot_count": 1,
        },
        "files": [
            {"file_name": "/u01/oradata/users01.dbf", "physical_reads": 500000, "physical_writes": 120000, "avg_read_ms": 4.2, "avg_write_ms": 2.1, "blocks_read": 450000, "blocks_written": 100000},
            {"file_name": "/u01/oradata/system01.dbf", "physical_reads": 350000, "physical_writes": 80000, "avg_read_ms": 3.8, "avg_write_ms": 1.9, "blocks_read": 300000, "blocks_written": 70000},
            {"file_name": "/u01/oradata/undotbs01.dbf", "physical_reads": 200000, "physical_writes": 100000, "avg_read_ms": 12.5, "avg_write_ms": 8.3, "blocks_read": 180000, "blocks_written": 90000},
        ],
        "hotspots": [
            {"file_name": "/u01/oradata/undotbs01.dbf", "avg_read_ms": 12.5, "avg_write_ms": 8.3},
        ],
    }


async def get_instance_parameters_handler(modified_only: bool = True) -> dict:
    """Get Oracle instance parameters.
    
    Queries V$PARAMETER for current parameter values.
    If modified_only=True, shows only non-default parameters.
    """
    try:
        from src.database.connection import get_connection_manager
        manager = get_connection_manager()
        
        if not manager.dsn or not manager.user:
            return _mock_instance_parameters()
        
        await manager.initialize()
        
        param_result = []
        try:
            if modified_only:
                param_query = """
                SELECT 
                    name,
                    value,
                    isdefault,
                    ismodified,
                    description
                FROM V$PARAMETER
                WHERE isdefault = 'FALSE'
                ORDER BY name
                """
            else:
                param_query = """
                SELECT 
                    name,
                    value,
                    isdefault,
                    ismodified,
                    description
                FROM V$PARAMETER
                ORDER BY name
                FETCH FIRST 50 ROWS ONLY
                """
            param_result = await manager.execute_query(param_query)
        except Exception as e:
            logger.warning(f"V$PARAMETER query failed: {e}")
        
        params = []
        for r in param_result:
            params.append({
                "name": r.get('NAME', 'Unknown'),
                "value": r.get('VALUE', ''),
                "is_default": r.get('ISDEFAULT', 'TRUE') == 'TRUE',
                "is_modified": r.get('ISMODIFIED', 'FALSE') != 'FALSE',
                "description": r.get('DESCRIPTION', ''),
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "data_source": "LIVE",
            "modified_only": modified_only,
            "total_parameters": len(params),
            "parameters": params,
        }
    except Exception as e:
        logger.warning(f"Instance parameters query failed, using mock: {e}")
        return _mock_instance_parameters()


def _mock_instance_parameters() -> dict:
    """Mock instance parameters."""
    return {
        "timestamp": datetime.now().isoformat(),
        "data_source": "MOCK",
        "modified_only": True,
        "total_parameters": 8,
        "parameters": [
            {"name": "db_block_size", "value": "8192", "is_default": False, "is_modified": True, "description": "Size of database block in bytes"},
            {"name": "memory_target", "value": "4294967296", "is_default": False, "is_modified": True, "description": "Target memory size"},
            {"name": "open_cursors", "value": "300", "is_default": False, "is_modified": True, "description": "Maximum number of open cursors per session"},
            {"name": "processes", "value": "500", "is_default": False, "is_modified": True, "description": "Maximum number of OS user processes"},
            {"name": "sga_target", "value": "2147483648", "is_default": False, "is_modified": True, "description": "Target SGA size"},
            {"name": "pga_aggregate_target", "value": "1073741824", "is_default": False, "is_modified": True, "description": "Target PGA aggregate size"},
            {"name": "undo_retention", "value": "900", "is_default": False, "is_modified": True, "description": "Undo retention in seconds"},
            {"name": "sessions", "value": "772", "is_default": False, "is_modified": True, "description": "Maximum number of sessions"},
        ],
    }


async def get_database_uptime_handler() -> dict:
    """Get database uptime and availability information.
    
    Queries V$INSTANCE for startup time and calculates uptime.
    """
    try:
        from src.database.connection import get_connection_manager
        manager = get_connection_manager()
        
        if not manager.dsn or not manager.user:
            return _mock_database_uptime()
        
        await manager.initialize()
        
        uptime_result = []
        try:
            uptime_query = """
            SELECT 
                instance_name,
                host_name,
                version,
                status,
                database_status,
                active_state,
                startup_time,
                ROUND((SYSDATE - startup_time) * 24, 2) as uptime_hours,
                ROUND((SYSDATE - startup_time), 2) as uptime_days,
                logins,
                archiver,
                instance_role
            FROM V$INSTANCE
            """
            uptime_result = await manager.execute_query(uptime_query)
        except Exception as e:
            logger.warning(f"V$INSTANCE uptime query failed: {e}")
        
        if uptime_result:
            row = uptime_result[0]
            return {
                "timestamp": datetime.now().isoformat(),
                "data_source": "LIVE",
                "instance_name": row.get('INSTANCE_NAME', 'Unknown'),
                "host_name": row.get('HOST_NAME', 'Unknown'),
                "version": row.get('VERSION', 'Unknown'),
                "status": row.get('STATUS', 'Unknown'),
                "database_status": row.get('DATABASE_STATUS', 'Unknown'),
                "active_state": row.get('ACTIVE_STATE', 'Unknown'),
                "startup_time": str(row.get('STARTUP_TIME', 'Unknown')),
                "uptime_hours": float(row.get('UPTIME_HOURS', 0)),
                "uptime_days": float(row.get('UPTIME_DAYS', 0)),
                "logins": row.get('LOGINS', 'Unknown'),
                "archiver": row.get('ARCHIVER', 'Unknown'),
                "instance_role": row.get('INSTANCE_ROLE', 'Unknown'),
            }
        
        return _mock_database_uptime()
    except Exception as e:
        logger.warning(f"Uptime query failed, using mock: {e}")
        return _mock_database_uptime()


def _mock_database_uptime() -> dict:
    """Mock uptime data."""
    return {
        "timestamp": datetime.now().isoformat(),
        "data_source": "MOCK",
        "instance_name": "BRMSIT",
        "host_name": "db-server-01",
        "version": "19.0.0.0.0",
        "status": "OPEN",
        "database_status": "ACTIVE",
        "active_state": "NORMAL",
        "startup_time": "2025-01-15 08:00:00",
        "uptime_hours": 8760.5,
        "uptime_days": 365.02,
        "logins": "ALLOWED",
        "archiver": "STARTED",
        "instance_role": "PRIMARY_INSTANCE",
    }


async def get_segment_sizes_handler(top_n: int = 20) -> dict:
    """Get top database segments by size.
    
    Queries DBA_SEGMENTS for largest tables, indexes, and LOBs.
    """
    try:
        from src.database.connection import get_connection_manager
        manager = get_connection_manager()
        
        if not manager.dsn or not manager.user:
            return _mock_segment_sizes()
        
        await manager.initialize()
        
        segment_result = []
        try:
            segment_query = """
            SELECT 
                owner,
                segment_name,
                segment_type,
                tablespace_name,
                ROUND(bytes/1024/1024, 2) as size_mb,
                ROUND(bytes/1024/1024/1024, 3) as size_gb,
                extents
            FROM DBA_SEGMENTS
            WHERE owner NOT IN ('SYS', 'SYSTEM', 'DBSNMP', 'OUTLN', 'MDSYS', 'ORDSYS', 'ORDDATA', 'CTXSYS', 'ANONYMOUS', 'EXFSYS', 'DMSYS', 'XDB', 'WMSYS')
            ORDER BY bytes DESC
            FETCH FIRST {n} ROWS ONLY
            """.format(n=top_n)
            segment_result = await manager.execute_query(segment_query)
        except Exception as e:
            logger.warning(f"DBA_SEGMENTS query failed: {e}")
        
        segments = []
        total_size_mb = 0
        for r in segment_result:
            size_mb = float(r.get('SIZE_MB', 0))
            total_size_mb += size_mb
            segments.append({
                "owner": r.get('OWNER', 'Unknown'),
                "segment_name": r.get('SEGMENT_NAME', 'Unknown'),
                "segment_type": r.get('SEGMENT_TYPE', 'Unknown'),
                "tablespace_name": r.get('TABLESPACE_NAME', 'Unknown'),
                "size_mb": size_mb,
                "size_gb": float(r.get('SIZE_GB', 0)),
                "extents": int(r.get('EXTENTS', 0)),
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "data_source": "LIVE",
            "top_n": top_n,
            "total_size_mb": round(total_size_mb, 2),
            "total_size_gb": round(total_size_mb / 1024, 3),
            "segments": segments,
        }
    except Exception as e:
        logger.warning(f"Segment sizes query failed, using mock: {e}")
        return _mock_segment_sizes()


def _mock_segment_sizes() -> dict:
    """Mock segment sizes."""
    return {
        "timestamp": datetime.now().isoformat(),
        "data_source": "MOCK",
        "top_n": 20,
        "total_size_mb": 15360,
        "total_size_gb": 15.0,
        "segments": [
            {"owner": "PIN", "segment_name": "EVENT_BAL_IMPACTS_T", "segment_type": "TABLE", "tablespace_name": "PIN_DATA", "size_mb": 4500, "size_gb": 4.395, "extents": 140},
            {"owner": "PIN", "segment_name": "EVENT_T", "segment_type": "TABLE", "tablespace_name": "PIN_DATA", "size_mb": 3200, "size_gb": 3.125, "extents": 100},
            {"owner": "PIN", "segment_name": "ITEM_T", "segment_type": "TABLE", "tablespace_name": "PIN_DATA", "size_mb": 2800, "size_gb": 2.734, "extents": 88},
            {"owner": "PIN", "segment_name": "IDX_EVENT_CREATED", "segment_type": "INDEX", "tablespace_name": "PIN_INDEX", "size_mb": 1500, "size_gb": 1.465, "extents": 47},
            {"owner": "PIN", "segment_name": "ACCOUNT_T", "segment_type": "TABLE", "tablespace_name": "PIN_DATA", "size_mb": 1200, "size_gb": 1.172, "extents": 38},
        ],
    }


async def get_temp_usage_handler() -> dict:
    """Get TEMP tablespace usage details.
    
    Queries V$SORT_SEGMENT and V$TEMP_SPACE_HEADER for temp space consumers.
    """
    try:
        from src.database.connection import get_connection_manager
        manager = get_connection_manager()
        
        if not manager.dsn or not manager.user:
            return _mock_temp_usage()
        
        await manager.initialize()
        
        # Overall temp usage
        temp_overview = []
        try:
            temp_query = """
            SELECT 
                tablespace_name,
                ROUND(tablespace_size/1024/1024, 2) as total_mb,
                ROUND(allocated_space/1024/1024, 2) as allocated_mb,
                ROUND(free_space/1024/1024, 2) as free_mb,
                ROUND((allocated_space/NULLIF(tablespace_size,0))*100, 2) as used_pct
            FROM DBA_TEMP_FREE_SPACE
            """
            temp_overview = await manager.execute_query(temp_query)
        except Exception as e:
            logger.warning(f"DBA_TEMP_FREE_SPACE query failed: {e}")
        
        # Top temp consumers by session
        temp_consumers = []
        try:
            consumer_query = """
            SELECT 
                s.sid,
                s.serial#,
                s.username,
                s.program,
                s.sql_id,
                ROUND(su.blocks * (SELECT value FROM V$PARAMETER WHERE name = 'db_block_size') / 1024 / 1024, 2) as temp_mb,
                su.segtype,
                su.tablespace
            FROM V$SORT_USAGE su
            JOIN V$SESSION s ON su.session_addr = s.saddr
            ORDER BY su.blocks DESC
            FETCH FIRST 10 ROWS ONLY
            """
            temp_consumers = await manager.execute_query(consumer_query)
        except Exception as e:
            logger.warning(f"V$SORT_USAGE query failed: {e}")
        
        overview = temp_overview[0] if temp_overview else {}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "data_source": "LIVE",
            "temp_tablespace": {
                "name": overview.get('TABLESPACE_NAME', 'TEMP'),
                "total_mb": float(overview.get('TOTAL_MB', 0)),
                "allocated_mb": float(overview.get('ALLOCATED_MB', 0)),
                "free_mb": float(overview.get('FREE_MB', 0)),
                "used_pct": float(overview.get('USED_PCT', 0)),
            },
            "top_consumers": [
                {
                    "sid": int(r.get('SID', 0)),
                    "serial": int(r.get('SERIAL#', 0)),
                    "username": r.get('USERNAME', 'Unknown'),
                    "program": r.get('PROGRAM', 'Unknown'),
                    "sql_id": r.get('SQL_ID', 'Unknown'),
                    "temp_mb": float(r.get('TEMP_MB', 0)),
                    "segment_type": r.get('SEGTYPE', 'Unknown'),
                }
                for r in temp_consumers
            ],
        }
    except Exception as e:
        logger.warning(f"Temp usage query failed, using mock: {e}")
        return _mock_temp_usage()


def _mock_temp_usage() -> dict:
    """Mock temp usage data."""
    return {
        "timestamp": datetime.now().isoformat(),
        "data_source": "MOCK",
        "temp_tablespace": {
            "name": "TEMP",
            "total_mb": 4096,
            "allocated_mb": 2800,
            "free_mb": 1296,
            "used_pct": 68.36,
        },
        "top_consumers": [
            {"sid": 145, "serial": 34521, "username": "APP_USER", "program": "java.exe", "sql_id": "abc123", "temp_mb": 850, "segment_type": "SORT"},
            {"sid": 267, "serial": 45678, "username": "REPORT_USER", "program": "sqlplus", "sql_id": "xyz789", "temp_mb": 620, "segment_type": "HASH"},
        ],
    }


# ============================================================================
# Server Entry Point
# ============================================================================

async def main():
    """Run the Performance MCP Server."""
    logger.info("Starting ODAOS Performance MCP Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            mcp.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
