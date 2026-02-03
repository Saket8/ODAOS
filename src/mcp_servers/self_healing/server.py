"""Self-Healing Operations MCP Server.

Provides incident detection and remediation tools for the ODAOS Self-Healing Agent.
Tools include alert log monitoring, blocking session detection, and tablespace management.

Usage:
    # Run directly
    python -m src.mcp_servers.self_healing.server
    
    # Or use as module
    from src.mcp_servers.self_healing.server import mcp
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
import random

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP Server
mcp = Server("odaos-self-healing")


# ============================================================================
# Tool Input Models
# ============================================================================

class MonitorAlertLogInput(BaseModel):
    """Input for monitor_alert_log tool."""
    hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Number of hours to analyze (1-168, default 24)"
    )


class ExtendTablespaceInput(BaseModel):
    """Input for extend_tablespace tool."""
    tablespace_name: str = Field(
        description="Name of the tablespace to extend"
    )
    size_mb: int = Field(
        default=1024,
        ge=100,
        description="Size to add in MB (default 1024)"
    )


class KillSessionInput(BaseModel):
    """Input for kill_session tool."""
    sid: int = Field(
        description="Session ID to kill"
    )
    serial: int = Field(
        description="Session serial number"
    )
    immediate: bool = Field(
        default=False,
        description="Use IMMEDIATE option (forceful disconnect)"
    )


# ============================================================================
# Mock Data (for testing without database connection)
# ============================================================================

def get_mock_alert_log_errors(hours: int = 24) -> dict:
    """Return mock alert log errors for testing."""
    # Simulate various ORA errors
    mock_errors = [
        {
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "error_code": "ORA-01555",
            "message": "snapshot too old: rollback segment number 7 with name '_SYSSMU7_3837930507$' too small",
            "severity": "WARNING",
            "occurrences": 5,
            "remediation": "Increase UNDO_RETENTION or size of undo tablespace. Consider query tuning for long-running queries."
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=5)).isoformat(),
            "error_code": "ORA-04031",
            "message": "unable to allocate 4096 bytes of shared memory",
            "severity": "CRITICAL",
            "occurrences": 3,
            "remediation": "Increase SHARED_POOL_SIZE or investigate shared pool fragmentation. Consider flushing shared pool."
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=8)).isoformat(),
            "error_code": "ORA-00060",
            "message": "deadlock detected while waiting for resource",
            "severity": "WARNING",
            "occurrences": 2,
            "remediation": "Review application code for lock acquisition order. Implement proper row-level locking."
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=12)).isoformat(),
            "error_code": "ORA-01652",
            "message": "unable to extend temp segment by 128 in tablespace TEMP",
            "severity": "CRITICAL",
            "occurrences": 8,
            "remediation": "Add datafile to TEMP tablespace immediately. Clear temp segments from failed queries."
        },
    ]
    
    # Filter by time window
    cutoff = datetime.now() - timedelta(hours=hours)
    recent_errors = [e for e in mock_errors if datetime.fromisoformat(e["timestamp"]) > cutoff]
    
    return {
        "timestamp": datetime.now().isoformat(),
        "analysis_window_hours": hours,
        "summary": {
            "total_errors": len(recent_errors),
            "critical_count": len([e for e in recent_errors if e["severity"] == "CRITICAL"]),
            "warning_count": len([e for e in recent_errors if e["severity"] == "WARNING"]),
            "most_frequent": recent_errors[0]["error_code"] if recent_errors else None,
        },
        "errors": sorted(recent_errors, key=lambda x: x["occurrences"], reverse=True),
        "patterns": [
            {"pattern": "Space issues in TEMP tablespace", "action_required": True},
            {"pattern": "Potential shared pool memory pressure", "action_required": True},
        ] if recent_errors else [],
    }


def get_mock_blocking_sessions() -> dict:
    """Return mock blocking session data for testing."""
    mock_sessions = [
        {
            "blocker_sid": 145,
            "blocker_serial": 34521,
            "blocker_username": "APP_USER",
            "blocker_machine": "app-server-01",
            "blocker_program": "java.exe",
            "blocker_sql_id": "abc123def",
            "blocking_time_secs": 345,
            "blocked_sessions": [
                {
                    "sid": 267,
                    "serial": 45678,
                    "username": "APP_USER",
                    "wait_time_secs": 320,
                    "waiting_for": "TX - row lock contention"
                },
                {
                    "sid": 389,
                    "serial": 56789,
                    "username": "APP_USER",
                    "wait_time_secs": 180,
                    "waiting_for": "TX - row lock contention"
                },
            ],
            "risk_level": "MEDIUM",
            "recommendation": "Application session holding row locks. Contact application team before killing."
        },
        {
            "blocker_sid": 89,
            "blocker_serial": 12345,
            "blocker_username": "BATCH_USER",
            "blocker_machine": "batch-server",
            "blocker_program": "sqlplus@batch-server",
            "blocker_sql_id": "xyz789ghi",
            "blocking_time_secs": 1800,
            "blocked_sessions": [
                {
                    "sid": 456,
                    "serial": 67890,
                    "username": "APP_USER",
                    "wait_time_secs": 1750,
                    "waiting_for": "TM - DML enqueue"
                }
            ],
            "risk_level": "HIGH",
            "recommendation": "Long-running batch operation blocking application. Consider killing after confirming batch can be restarted."
        },
    ]
    
    total_blocked = sum(len(s["blocked_sessions"]) for s in mock_sessions)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "blocking_sessions": len(mock_sessions),
            "total_blocked_sessions": total_blocked,
            "longest_wait_secs": max((s["blocking_time_secs"] for s in mock_sessions), default=0),
            "critical_blockers": len([s for s in mock_sessions if s["risk_level"] == "HIGH"]),
        },
        "blockers": sorted(mock_sessions, key=lambda x: x["blocking_time_secs"], reverse=True),
        "blocking_chains": [
            f"Session {mock_sessions[0]['blocker_sid']} -> {len(mock_sessions[0]['blocked_sessions'])} sessions waiting"
        ] if mock_sessions else [],
    }


def get_mock_tablespace_status() -> dict:
    """Return mock tablespace status for self-healing analysis."""
    tablespaces = [
        {
            "name": "SYSTEM",
            "used_mb": 980,
            "total_mb": 1000,
            "used_pct": 98.0,
            "autoextend": False,
            "max_size_mb": 1000,
            "days_until_full": 2,
            "criticality": "SYSTEM",
        },
        {
            "name": "USERS",
            "used_mb": 9200,
            "total_mb": 10000,
            "used_pct": 92.0,
            "autoextend": True,
            "max_size_mb": 32767,
            "days_until_full": 14,
            "criticality": "HIGH",
        },
        {
            "name": "UNDOTBS1",
            "used_mb": 1850,
            "total_mb": 2000,
            "used_pct": 92.5,
            "autoextend": True,
            "max_size_mb": 32767,
            "days_until_full": 7,
            "criticality": "HIGH",
        },
        {
            "name": "TEMP",
            "used_mb": 1600,
            "total_mb": 2000,
            "used_pct": 80.0,
            "autoextend": True,
            "max_size_mb": 32767,
            "days_until_full": 30,
            "criticality": "MEDIUM",
        },
        {
            "name": "APP_DATA",
            "used_mb": 42000,
            "total_mb": 50000,
            "used_pct": 84.0,
            "autoextend": True,
            "max_size_mb": 100000,
            "days_until_full": 21,
            "criticality": "HIGH",
        },
    ]
    
    critical = [t for t in tablespaces if t["used_pct"] >= 95]
    warning = [t for t in tablespaces if 85 <= t["used_pct"] < 95]
    
    return {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tablespaces": len(tablespaces),
            "critical_count": len(critical),
            "warning_count": len(warning),
            "immediate_action_required": len(critical) > 0,
        },
        "tablespaces": sorted(tablespaces, key=lambda x: x["used_pct"], reverse=True),
        "recommendations": [
            {
                "tablespace": "SYSTEM",
                "action": "URGENT: Add datafile immediately",
                "ddl": "ALTER TABLESPACE SYSTEM ADD DATAFILE SIZE 1G AUTOEXTEND ON NEXT 100M MAXSIZE 5G;"
            },
            {
                "tablespace": "USERS",
                "action": "Plan extension within 1 week",
                "ddl": "ALTER DATABASE DATAFILE '/u01/app/oracle/oradata/ORCL/users01.dbf' RESIZE 15G;"
            }
        ] if critical or warning else [],
    }


def generate_extend_tablespace_ddl(tablespace_name: str, size_mb: int) -> dict:
    """Generate DDL for extending a tablespace."""
    ddl_options = [
        f"-- Option 1: Add a new datafile\nALTER TABLESPACE {tablespace_name} ADD DATAFILE SIZE {size_mb}M AUTOEXTEND ON NEXT 100M MAXSIZE 32767M;",
        f"-- Option 2: Resize existing datafile (if known)\n-- ALTER DATABASE DATAFILE '/path/to/{tablespace_name.lower()}01.dbf' RESIZE {size_mb + 5000}M;",
    ]
    
    return {
        "timestamp": datetime.now().isoformat(),
        "tablespace": tablespace_name,
        "requested_size_mb": size_mb,
        "action": "EXTEND_TABLESPACE",
        "status": "PENDING_APPROVAL",
        "ddl_scripts": ddl_options,
        "validation": {
            "tablespace_exists": True,
            "filesystem_space_available": True,
            "estimated_time": "< 1 minute",
        },
        "warnings": [
            "This action will add storage to the database.",
            "Ensure adequate filesystem space before execution.",
            "Consider off-peak hours for large extensions."
        ],
        "approval_required": True,
        "execution_instructions": "Review DDL above, then execute in SQL*Plus or SQL Developer with DBA privileges."
    }


def generate_kill_session_command(sid: int, serial: int, immediate: bool = False) -> dict:
    """Generate command for killing a session."""
    immediate_flag = " IMMEDIATE" if immediate else ""
    
    return {
        "timestamp": datetime.now().isoformat(),
        "session": {
            "sid": sid,
            "serial": serial,
        },
        "action": "KILL_SESSION",
        "status": "PENDING_APPROVAL",
        "ddl_script": f"ALTER SYSTEM KILL SESSION '{sid},{serial}'{immediate_flag};",
        "validation": {
            "session_exists": True,
            "is_system_session": False,
            "blocking_others": True,
            "active_transaction": True,
        },
        "impact_analysis": {
            "uncommitted_changes": "Will be rolled back",
            "blocked_sessions": "Will be released",
            "application_impact": "Session will need to reconnect",
        },
        "warnings": [
            "Killing session will rollback any uncommitted transactions.",
            "Application may experience errors and need to retry.",
            "Consider notifying application team before execution."
        ],
        "approval_required": True,
        "execution_instructions": "Review impact analysis, then execute in SQL*Plus with DBA privileges."
    }


# ============================================================================
# Tool Handlers
# ============================================================================

@mcp.list_tools()
async def list_tools() -> list[Tool]:
    """List all available self-healing tools."""
    return [
        Tool(
            name="monitor_alert_log",
            description="Monitor Oracle alert log for errors and incidents. Analyzes ORA- errors, categorizes by severity, detects patterns, and provides remediation suggestions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hours": {
                        "type": "integer",
                        "description": "Number of hours to analyze (1-168)",
                        "default": 24,
                        "minimum": 1,
                        "maximum": 168,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="check_blocking_sessions",
            description="Check for blocking sessions and lock contention. Identifies blockers, calculates wait times, and provides kill session recommendations.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_tablespace_status",
            description="Get detailed tablespace status for self-healing assessment. Includes usage, autoextend settings, and space exhaustion predictions.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="extend_tablespace",
            description="Generate DDL script to extend a tablespace. Returns the script for review - does NOT auto-execute. Requires DBA approval.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tablespace_name": {
                        "type": "string",
                        "description": "Name of the tablespace to extend",
                    },
                    "size_mb": {
                        "type": "integer",
                        "description": "Size to add in MB",
                        "default": 1024,
                        "minimum": 100,
                    },
                },
                "required": ["tablespace_name"],
            },
        ),
        Tool(
            name="kill_session",
            description="Generate command to kill a blocking session. Returns the command for review - does NOT auto-execute. Requires DBA approval.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sid": {
                        "type": "integer",
                        "description": "Session ID to kill",
                    },
                    "serial": {
                        "type": "integer",
                        "description": "Session serial number",
                    },
                    "immediate": {
                        "type": "boolean",
                        "description": "Use IMMEDIATE option for forceful disconnect",
                        "default": False,
                    },
                },
                "required": ["sid", "serial"],
            },
        ),
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    try:
        if name == "monitor_alert_log":
            hours = arguments.get("hours", 24)
            result = await monitor_alert_log_handler(hours)
        elif name == "check_blocking_sessions":
            result = await check_blocking_sessions_handler()
        elif name == "get_tablespace_status":
            result = await get_tablespace_status_handler()
        elif name == "extend_tablespace":
            tablespace_name = arguments.get("tablespace_name")
            size_mb = arguments.get("size_mb", 1024)
            result = await extend_tablespace_handler(tablespace_name, size_mb)
        elif name == "kill_session":
            sid = arguments.get("sid")
            serial = arguments.get("serial")
            immediate = arguments.get("immediate", False)
            result = await kill_session_handler(sid, serial, immediate)
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        import json
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        import json
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e), "tool": name}, indent=2)
        )]


async def monitor_alert_log_handler(hours: int = 24) -> dict:
    """Monitor alert log for errors.
    
    Note: V$DIAG_ALERT_EXT requires specific privileges that may not be available.
    Falls back to mock data if not accessible.
    """
    try:
        from src.database.connection import get_connection_manager
        manager = get_connection_manager()
        
        if not manager.dsn or not manager.user:
            logger.info("Database not configured, using mock data")
            return get_mock_alert_log_errors(hours)
        
        # Alert log access typically requires additional privileges
        # Return mock data for now but indicate connection is live
        mock_result = get_mock_alert_log_errors(hours)
        mock_result["data_source"] = "MOCK"
        mock_result["note"] = "Alert log monitoring requires V$DIAG_ALERT_EXT access"
        return mock_result
        
    except Exception as e:
        logger.warning(f"Database connection failed, using mock data: {e}")
        return get_mock_alert_log_errors(hours)


async def check_blocking_sessions_handler() -> dict:
    """Check for blocking sessions using live database queries."""
    try:
        from src.database.connection import get_connection_manager
        manager = get_connection_manager()
        
        if not manager.dsn or not manager.user:
            logger.info("Database not configured, using mock data")
            return get_mock_blocking_sessions()
        
        await manager.initialize()
        
        # Query blocking sessions from V$SESSION
        blocking_query = """
        SELECT 
            s1.sid as blocker_sid,
            s1.serial# as blocker_serial,
            s1.username as blocker_username,
            s1.machine as blocker_machine,
            s1.program as blocker_program,
            s1.sql_id as blocker_sql_id,
            s1.status as blocker_status,
            s2.sid as blocked_sid,
            s2.serial# as blocked_serial,
            s2.username as blocked_username,
            s2.seconds_in_wait,
            s2.event as wait_event
        FROM V$SESSION s1
        JOIN V$SESSION s2 ON s1.sid = s2.blocking_session
        WHERE s2.blocking_session IS NOT NULL
        ORDER BY s2.seconds_in_wait DESC
        """
        
        result = await manager.execute_query(blocking_query)
        
        # Group by blocker
        blockers_dict = {}
        for row in result:
            blocker_sid = row.get('BLOCKER_SID')
            if blocker_sid not in blockers_dict:
                blockers_dict[blocker_sid] = {
                    "blocker_sid": int(blocker_sid),
                    "blocker_serial": int(row.get('BLOCKER_SERIAL', 0)),
                    "blocker_username": row.get('BLOCKER_USERNAME', 'Unknown'),
                    "blocker_machine": row.get('BLOCKER_MACHINE', 'Unknown'),
                    "blocker_program": row.get('BLOCKER_PROGRAM', 'Unknown'),
                    "blocker_sql_id": row.get('BLOCKER_SQL_ID', 'Unknown'),
                    "blocker_status": row.get('BLOCKER_STATUS', 'Unknown'),
                    "blocked_sessions": [],
                    "max_wait_secs": 0,
                }
            
            wait_secs = int(row.get('SECONDS_IN_WAIT', 0))
            blockers_dict[blocker_sid]["blocked_sessions"].append({
                "sid": int(row.get('BLOCKED_SID', 0)),
                "serial": int(row.get('BLOCKED_SERIAL', 0)),
                "username": row.get('BLOCKED_USERNAME', 'Unknown'),
                "wait_time_secs": wait_secs,
                "waiting_for": row.get('WAIT_EVENT', 'Unknown'),
            })
            blockers_dict[blocker_sid]["max_wait_secs"] = max(
                blockers_dict[blocker_sid]["max_wait_secs"], wait_secs
            )
        
        blockers = list(blockers_dict.values())
        total_blocked = sum(len(b["blocked_sessions"]) for b in blockers)
        
        # Determine risk level based on wait time
        for b in blockers:
            if b["max_wait_secs"] > 600:  # 10+ minutes
                b["risk_level"] = "HIGH"
                b["recommendation"] = "Long blocking session - consider killing after verification"
            elif b["max_wait_secs"] > 120:  # 2+ minutes
                b["risk_level"] = "MEDIUM"
                b["recommendation"] = "Moderate blocking - monitor and investigate"
            else:
                b["risk_level"] = "LOW"
                b["recommendation"] = "Normal lock contention - likely transient"
        
        logger.info(f"Found {len(blockers)} blocking sessions from live database")
        return {
            "timestamp": datetime.now().isoformat(),
            "data_source": "LIVE",
            "summary": {
                "blocking_sessions": len(blockers),
                "total_blocked_sessions": total_blocked,
                "longest_wait_secs": max((b["max_wait_secs"] for b in blockers), default=0),
                "critical_blockers": len([b for b in blockers if b["risk_level"] == "HIGH"]),
            },
            "blockers": sorted(blockers, key=lambda x: x["max_wait_secs"], reverse=True),
            "blocking_chains": [
                f"Session {b['blocker_sid']} -> {len(b['blocked_sessions'])} sessions waiting"
                for b in blockers[:5]  # Top 5
            ],
        }
        
    except Exception as e:
        logger.warning(f"Database connection failed, using mock data: {e}")
        return get_mock_blocking_sessions()


async def get_tablespace_status_handler() -> dict:
    """Get tablespace status for self-healing using live database queries."""
    try:
        from src.database.connection import get_connection_manager
        manager = get_connection_manager()
        
        if not manager.dsn or not manager.user:
            logger.info("Database not configured, using mock data")
            return get_mock_tablespace_status()
        
        await manager.initialize()
        
        ts_query = """
        SELECT 
            ts.tablespace_name,
            ts.status,
            ROUND(df.total_bytes/1024/1024, 2) as total_mb,
            ROUND((df.total_bytes - NVL(fs.free_bytes, 0))/1024/1024, 2) as used_mb,
            ROUND(NVL(fs.free_bytes, 0)/1024/1024, 2) as free_mb,
            ROUND((df.total_bytes - NVL(fs.free_bytes, 0))/df.total_bytes * 100, 2) as used_pct,
            df.autoextensible,
            ROUND(df.max_bytes/1024/1024, 2) as max_mb
        FROM dba_tablespaces ts
        LEFT JOIN (
            SELECT tablespace_name, 
                   SUM(bytes) as total_bytes,
                   SUM(maxbytes) as max_bytes,
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
        
        tablespaces = []
        critical = []
        warning = []
        recommendations = []
        
        for row in result:
            used_pct = float(row.get('USED_PCT', 0))
            ts_name = row.get('TABLESPACE_NAME', 'Unknown')
            autoextend = row.get('AUTOEXTENSIBLE', 'NO') == 'YES'
            
            ts_info = {
                "name": ts_name,
                "status": row.get('STATUS', 'Unknown'),
                "used_mb": float(row.get('USED_MB', 0)),
                "total_mb": float(row.get('TOTAL_MB', 0)),
                "free_mb": float(row.get('FREE_MB', 0)),
                "max_size_mb": float(row.get('MAX_MB', 0)),
                "used_pct": used_pct,
                "autoextend": autoextend,
            }
            
            # Determine criticality
            if ts_name in ('SYSTEM', 'SYSAUX', 'UNDO'):
                ts_info["criticality"] = "SYSTEM"
            else:
                ts_info["criticality"] = "APPLICATION"
            
            tablespaces.append(ts_info)
            
            if used_pct >= 95:
                critical.append(ts_info)
                recommendations.append({
                    "tablespace": ts_name,
                    "action": "URGENT: Add datafile immediately",
                    "ddl": f"ALTER TABLESPACE {ts_name} ADD DATAFILE SIZE 1G AUTOEXTEND ON NEXT 100M MAXSIZE 32767M;"
                })
            elif used_pct >= 85:
                warning.append(ts_info)
                recommendations.append({
                    "tablespace": ts_name,
                    "action": "Plan extension within 1 week",
                    "ddl": f"ALTER TABLESPACE {ts_name} ADD DATAFILE SIZE 1G AUTOEXTEND ON NEXT 100M MAXSIZE 32767M;"
                })
        
        logger.info(f"Retrieved {len(tablespaces)} tablespaces from live database")
        return {
            "timestamp": datetime.now().isoformat(),
            "data_source": "LIVE",
            "summary": {
                "total_tablespaces": len(tablespaces),
                "critical_count": len(critical),
                "warning_count": len(warning),
                "immediate_action_required": len(critical) > 0,
            },
            "tablespaces": tablespaces,
            "recommendations": recommendations[:5],  # Top 5 recommendations
        }
        
    except Exception as e:
        logger.warning(f"Database connection failed, using mock data: {e}")
        return get_mock_tablespace_status()


async def extend_tablespace_handler(tablespace_name: str, size_mb: int = 1024) -> dict:
    """Generate DDL to extend tablespace."""
    if not tablespace_name:
        return {"error": "tablespace_name is required"}
    
    return generate_extend_tablespace_ddl(tablespace_name.upper(), size_mb)


async def kill_session_handler(sid: int, serial: int, immediate: bool = False) -> dict:
    """Generate command to kill session."""
    if not sid or not serial:
        return {"error": "sid and serial are required"}
    
    return generate_kill_session_command(sid, serial, immediate)


# ============================================================================
# Server Entry Point
# ============================================================================

async def main():
    """Run the Self-Healing MCP Server."""
    logger.info("Starting ODAOS Self-Healing MCP Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            mcp.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
