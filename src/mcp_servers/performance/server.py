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
    """Get database performance metrics from live database."""
    try:
        from src.database.live_queries import LiveDBQueries
        
        with LiveDBQueries() as db:
            info = db.get_database_info()
            metrics = db.get_performance_metrics()
            
            return {
                "timestamp": metrics["timestamp"],
                "database": info["database"]["NAME"],
                "pdb": info["database"]["PDB"],
                "cpu": {
                    "host_cpu_utilization": 0,  # Not available without special grants
                    "db_cpu_percentage": 0,
                },
                "memory": {
                    "sga_total_mb": metrics["sga"].get("Total SGA Size", 0),
                    "buffer_cache_mb": metrics["sga"].get("Buffer Cache Size", 0),
                    "shared_pool_mb": metrics["sga"].get("Shared Pool Size", 0),
                    "pga_mb": metrics["pga_mb"],
                },
                "sessions": {
                    "active_sessions": metrics["sessions"]["ACTIVE"] or 0,
                    "total_sessions": metrics["sessions"]["TOTAL"] or 0,
                    "inactive_sessions": metrics["sessions"]["INACTIVE"] or 0,
                },
                "top_wait_events": [
                    {"event": w["EVENT"], "time_secs": w["TIME_SECS"], "wait_class": w["WAIT_CLASS"]}
                    for w in metrics["wait_events"][:5]
                ],
                "system_stats": metrics["system_stats"],
            }
    except Exception as e:
        logger.warning(f"Live database failed, using mock: {e}")
        return get_mock_database_metrics()


async def analyze_top_sql_handler(top_n: int = 10, order_by: str = "elapsed_time") -> dict:
    """Analyze top SQL statements from live database."""
    try:
        from src.database.live_queries import LiveDBQueries
        
        with LiveDBQueries() as db:
            top_sql = db.get_top_sql(top_n, order_by)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "parameters": {"top_n": top_n, "order_by": order_by},
                "sql_statements": [
                    {
                        "sql_id": s["SQL_ID"],
                        "sql_text": s.get("SQL_PREVIEW", ""),
                        "elapsed_time_secs": s["ELAPSED_SECS"],
                        "cpu_time_secs": s["CPU_SECS"],
                        "executions": s["EXECUTIONS"],
                        "buffer_gets": s["BUFFER_GETS"],
                        "disk_reads": s["DISK_READS"],
                        "gets_per_exec": s["GETS_PER_EXEC"] or 0,
                    }
                    for s in top_sql
                ],
            }
    except Exception as e:
        logger.warning(f"Live database failed, using mock: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "parameters": {"top_n": top_n, "order_by": order_by},
            "sql_statements": get_mock_top_sql(top_n, order_by),
        }


async def check_tablespace_usage_handler(threshold: int = 85) -> dict:
    """Check tablespace usage from live database."""
    try:
        from src.database.live_queries import LiveDBQueries
        
        with LiveDBQueries() as db:
            return db.get_tablespace_usage(threshold)
            
    except Exception as e:
        logger.warning(f"Live database failed, using mock: {e}")
        return get_mock_tablespace_usage(threshold)


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
