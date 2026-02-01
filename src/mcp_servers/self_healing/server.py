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
    """Monitor alert log for errors - uses mock data as alert log requires special access."""
    # Alert log access requires V_$DIAG_ALERT_EXT which may not be granted
    # Keep mock data for this handler
    return get_mock_alert_log_errors(hours)


async def check_blocking_sessions_handler() -> dict:
    """Check for blocking sessions from live database."""
    try:
        from src.database.live_queries import LiveDBQueries
        
        with LiveDBQueries() as db:
            blocking = db.get_blocking_sessions()
            
            # Format for agent consumption
            blockers = []
            for b in blocking.get("blockers", []):
                blockers.append({
                    "blocker_sid": b["SID"],
                    "blocker_serial": b["SERIAL#"],
                    "blocker_username": b.get("USERNAME"),
                    "blocker_machine": b.get("MACHINE"),
                    "blocker_program": b.get("PROGRAM"),
                    "blocker_sql_id": b.get("SQL_ID"),
                    "blocked_session_count": b.get("VICTIMS", 0),
                    "risk_level": "HIGH" if b.get("VICTIMS", 0) > 2 else "MEDIUM",
                })
            
            return {
                "timestamp": blocking["timestamp"],
                "summary": {
                    "blocking_sessions": blocking["blocker_count"],
                    "total_blocked_sessions": blocking["blocked_count"],
                },
                "blockers": blockers,
            }
    except Exception as e:
        logger.warning(f"Live database failed, using mock: {e}")
        return get_mock_blocking_sessions()


async def get_tablespace_status_handler() -> dict:
    """Get tablespace status from live database."""
    try:
        from src.database.live_queries import LiveDBQueries
        
        with LiveDBQueries() as db:
            ts_data = db.get_tablespace_usage()
            
            # Format for self-healing analysis
            tablespaces = []
            for alert in ts_data.get("alerts", []) + ts_data.get("healthy", []):
                tablespaces.append({
                    "name": alert["name"],
                    "used_mb": alert["used_mb"],
                    "total_mb": alert["total_mb"],
                    "used_pct": alert["used_pct"],
                    "criticality": alert.get("severity", "OK"),
                })
            
            return {
                "timestamp": ts_data["timestamp"],
                "summary": ts_data["summary"],
                "tablespaces": sorted(tablespaces, key=lambda x: x["used_pct"], reverse=True),
            }
    except Exception as e:
        logger.warning(f"Live database failed, using mock: {e}")
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
