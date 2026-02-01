"""Cost Optimization MCP Server.

Provides OCI cost analysis and resource utilization tools for the ODAOS Cost Optimization Agent.
Tools include cost queries, compute utilization analysis, and idle resource detection.

Usage:
    # Run directly
    python -m src.mcp_servers.cost_optimization.server
    
    # Or use as module
    from src.mcp_servers.cost_optimization.server import mcp
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
mcp = Server("odaos-cost-optimization")


# ============================================================================
# Tool Input Models
# ============================================================================

class GetOCICostsInput(BaseModel):
    """Input for get_oci_costs tool."""
    days: int = Field(
        default=30,
        ge=1,
        le=90,
        description="Number of days to analyze (1-90, default 30)"
    )
    group_by: str = Field(
        default="service",
        description="Group costs by: service, compartment, or tag"
    )


class AnalyzeComputeInput(BaseModel):
    """Input for analyze_compute_utilization tool."""
    compartment_id: Optional[str] = Field(
        default=None,
        description="Compartment OCID (optional, defaults to root)"
    )
    threshold: int = Field(
        default=30,
        ge=0,
        le=100,
        description="CPU threshold for underutilized (default 30%)"
    )


class ListIdleResourcesInput(BaseModel):
    """Input for list_idle_resources tool."""
    compartment_id: Optional[str] = Field(
        default=None,
        description="Compartment OCID (optional, defaults to root)"
    )


class ForecastCostsInput(BaseModel):
    """Input for forecast_costs tool."""
    days_ahead: int = Field(
        default=30,
        ge=7,
        le=90,
        description="Days to forecast (7-90, default 30)"
    )
    budget_amount: Optional[float] = Field(
        default=None,
        description="Monthly budget for comparison"
    )


# ============================================================================
# Mock Data (for testing without OCI API)
# ============================================================================

def get_mock_oci_costs(days: int = 30, group_by: str = "service") -> dict:
    """Return mock OCI cost data for testing."""
    service_costs = [
        {"name": "Database", "cost": 4567.89, "change_pct": 12.3},
        {"name": "Compute", "cost": 2345.67, "change_pct": -5.2},
        {"name": "Object Storage", "cost": 456.78, "change_pct": 8.1},
        {"name": "Block Volumes", "cost": 234.56, "change_pct": 2.4},
        {"name": "Networking", "cost": 123.45, "change_pct": -1.5},
        {"name": "Autonomous Database", "cost": 890.12, "change_pct": 15.6},
        {"name": "Load Balancer", "cost": 78.90, "change_pct": 0.0},
    ]
    
    compartment_costs = [
        {"name": "Production", "cost": 5234.56, "change_pct": 8.5},
        {"name": "Development", "cost": 1234.56, "change_pct": -12.3},
        {"name": "Testing", "cost": 567.89, "change_pct": 3.2},
        {"name": "Shared Services", "cost": 1234.56, "change_pct": 1.1},
    ]
    
    costs = service_costs if group_by == "service" else compartment_costs
    total_cost = sum(c["cost"] for c in costs)
    daily_avg = total_cost / days
    
    # Generate trend data
    trend_data = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=6-i)).strftime("%Y-%m-%d")
        trend_data.append({
            "date": date,
            "cost": round(daily_avg * (1 + random.uniform(-0.1, 0.1)), 2)
        })
    
    return {
        "timestamp": datetime.now().isoformat(),
        "period": {
            "days": days,
            "start_date": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
        },
        "summary": {
            "total_cost": round(total_cost, 2),
            "daily_average": round(daily_avg, 2),
            "projected_monthly": round(daily_avg * 30, 2),
            "currency": "USD",
        },
        f"by_{group_by}": sorted(costs, key=lambda x: x["cost"], reverse=True),
        "trend": trend_data,
        "insights": [
            {"type": "increase", "message": "Database costs up 12.3% - consider reserved capacity"},
            {"type": "opportunity", "message": "Autonomous DB costs growing - evaluate OCPU scaling"},
        ],
    }


def get_mock_compute_utilization(threshold: int = 30) -> dict:
    """Return mock compute utilization data for testing."""
    resources = [
        {
            "name": "db-prod-01",
            "type": "DB System",
            "shape": "VM.Standard.E4.Flex",
            "ocpu": 4,
            "avg_cpu_pct": 15.2,
            "peak_cpu_pct": 45.8,
            "avg_memory_pct": 22.5,
            "monthly_cost": 456.78,
            "potential_savings": 228.39,
            "recommendation": "Downsize to 2 OCPU - save 50%"
        },
        {
            "name": "db-dev-01",
            "type": "DB System",
            "shape": "VM.Standard.E4.Flex",
            "ocpu": 2,
            "avg_cpu_pct": 8.5,
            "peak_cpu_pct": 25.0,
            "avg_memory_pct": 12.3,
            "monthly_cost": 234.56,
            "potential_savings": 117.28,
            "recommendation": "Consider stopping during non-business hours"
        },
        {
            "name": "app-server-02",
            "type": "Compute Instance",
            "shape": "VM.Standard.E4.Flex",
            "ocpu": 8,
            "avg_cpu_pct": 65.4,
            "peak_cpu_pct": 92.1,
            "avg_memory_pct": 78.5,
            "monthly_cost": 567.89,
            "potential_savings": 0,
            "recommendation": "Well-utilized - no changes recommended"
        },
    ]
    
    underutilized = [r for r in resources if r["avg_cpu_pct"] < threshold]
    total_savings = sum(r["potential_savings"] for r in underutilized)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "analysis_period": "Last 7 days",
        "threshold": threshold,
        "summary": {
            "total_resources": len(resources),
            "underutilized_count": len(underutilized),
            "potential_monthly_savings": round(total_savings, 2),
            "potential_annual_savings": round(total_savings * 12, 2),
        },
        "underutilized_resources": underutilized,
        "well_utilized_resources": [r for r in resources if r["avg_cpu_pct"] >= threshold],
        "recommendations": [
            {
                "priority": "HIGH",
                "action": f"Rightsize {len(underutilized)} underutilized resources",
                "savings": round(total_savings, 2),
            },
            {
                "priority": "MEDIUM",
                "action": "Implement auto-scaling for variable workloads",
                "savings": None,
            }
        ],
    }


def get_mock_idle_resources() -> dict:
    """Return mock idle resource data for testing."""
    idle_instances = [
        {
            "name": "test-server-03",
            "type": "Compute Instance",
            "state": "STOPPED",
            "stopped_since": (datetime.now() - timedelta(days=15)).isoformat(),
            "days_idle": 15,
            "monthly_cost_when_running": 123.45,
            "storage_cost": 12.34,
            "recommendation": "Terminate if no longer needed"
        },
        {
            "name": "legacy-db-backup",
            "type": "Compute Instance",
            "state": "STOPPED",
            "stopped_since": (datetime.now() - timedelta(days=45)).isoformat(),
            "days_idle": 45,
            "monthly_cost_when_running": 234.56,
            "storage_cost": 23.45,
            "recommendation": "Archive to Object Storage and terminate"
        },
    ]
    
    unattached_volumes = [
        {
            "name": "old-data-volume",
            "type": "Block Volume",
            "size_gb": 500,
            "created": (datetime.now() - timedelta(days=60)).isoformat(),
            "days_unattached": 60,
            "monthly_cost": 45.67,
            "recommendation": "Delete after confirming data is backed up"
        },
        {
            "name": "dev-scratch-01",
            "type": "Block Volume",
            "size_gb": 100,
            "created": (datetime.now() - timedelta(days=30)).isoformat(),
            "days_unattached": 30,
            "monthly_cost": 9.12,
            "recommendation": "Delete if no longer needed"
        },
    ]
    
    unused_boot_volumes = [
        {
            "name": "boot-old-app-server",
            "type": "Boot Volume",
            "size_gb": 50,
            "created": (datetime.now() - timedelta(days=90)).isoformat(),
            "days_orphaned": 90,
            "monthly_cost": 4.56,
            "recommendation": "Delete - instance was terminated"
        },
    ]
    
    total_idle_cost = (
        sum(r["storage_cost"] for r in idle_instances) +
        sum(r["monthly_cost"] for r in unattached_volumes) +
        sum(r["monthly_cost"] for r in unused_boot_volumes)
    )
    
    return {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "stopped_instances": len(idle_instances),
            "unattached_volumes": len(unattached_volumes),
            "orphan_boot_volumes": len(unused_boot_volumes),
            "total_idle_monthly_cost": round(total_idle_cost, 2),
            "total_idle_annual_cost": round(total_idle_cost * 12, 2),
        },
        "stopped_instances": idle_instances,
        "unattached_block_volumes": unattached_volumes,
        "orphan_boot_volumes": unused_boot_volumes,
        "cleanup_scripts": [
            "# Terminate stopped instances (after confirmation)",
            "oci compute instance terminate --instance-id <ocid> --force",
            "",
            "# Delete unattached volumes",
            "oci bv volume delete --volume-id <ocid> --force",
        ],
    }


def get_mock_cost_forecast(days_ahead: int = 30, budget: Optional[float] = None) -> dict:
    """Return mock cost forecast for testing."""
    daily_avg = 275.50
    current_month_spend = daily_avg * datetime.now().day
    
    # Simple linear forecast
    forecasts = []
    for period in [30, 60, 90]:
        projected = daily_avg * period
        forecasts.append({
            "period_days": period,
            "projected_cost": round(projected, 2),
            "confidence": "HIGH" if period <= 30 else "MEDIUM",
        })
    
    budget_analysis = None
    if budget:
        projected_30d = daily_avg * 30
        budget_analysis = {
            "monthly_budget": budget,
            "projected_spend": round(projected_30d, 2),
            "variance": round(projected_30d - budget, 2),
            "variance_pct": round((projected_30d - budget) / budget * 100, 2),
            "status": "ON_TRACK" if projected_30d <= budget else "OVER_BUDGET",
            "alert": projected_30d > budget * 0.9,
        }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "current_month": {
            "month": datetime.now().strftime("%B %Y"),
            "days_elapsed": datetime.now().day,
            "spend_to_date": round(current_month_spend, 2),
            "daily_average": round(daily_avg, 2),
        },
        "forecasts": forecasts,
        "budget_analysis": budget_analysis,
        "cost_drivers": [
            {"service": "Database", "contribution_pct": 45.2, "trend": "INCREASING"},
            {"service": "Compute", "contribution_pct": 28.5, "trend": "STABLE"},
            {"service": "Storage", "contribution_pct": 15.3, "trend": "STABLE"},
        ],
        "recommendations": [
            "Consider Reserved Capacity for Database to save up to 50%",
            "Evaluate Flexible shapes for Compute rightsizing",
            "Review lifecycle policies for Object Storage tiering",
        ],
    }


# ============================================================================
# Tool Handlers
# ============================================================================

@mcp.list_tools()
async def list_tools() -> list[Tool]:
    """List all available cost optimization tools."""
    return [
        Tool(
            name="get_oci_costs",
            description="Get OCI cost breakdown and trends. Returns costs grouped by service or compartment, daily trends, and cost insights.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to analyze (1-90)",
                        "default": 30,
                        "minimum": 1,
                        "maximum": 90,
                    },
                    "group_by": {
                        "type": "string",
                        "description": "Group costs by service or compartment",
                        "enum": ["service", "compartment"],
                        "default": "service",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="analyze_compute_utilization",
            description="Analyze compute and database resource utilization. Identifies underutilized resources and calculates potential rightsizing savings.",
            inputSchema={
                "type": "object",
                "properties": {
                    "compartment_id": {
                        "type": "string",
                        "description": "Compartment OCID (optional)",
                    },
                    "threshold": {
                        "type": "integer",
                        "description": "CPU threshold for underutilized (default 30%)",
                        "default": 30,
                        "minimum": 0,
                        "maximum": 100,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="list_idle_resources",
            description="Find idle and unused OCI resources. Identifies stopped instances, unattached volumes, and orphan boot volumes with cleanup recommendations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "compartment_id": {
                        "type": "string",
                        "description": "Compartment OCID (optional)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="forecast_costs",
            description="Forecast future OCI costs based on current trends. Provides projections and budget variance analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days_ahead": {
                        "type": "integer",
                        "description": "Days to forecast (7-90)",
                        "default": 30,
                        "minimum": 7,
                        "maximum": 90,
                    },
                    "budget_amount": {
                        "type": "number",
                        "description": "Monthly budget for comparison",
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
        if name == "get_oci_costs":
            days = arguments.get("days", 30)
            group_by = arguments.get("group_by", "service")
            result = await get_oci_costs_handler(days, group_by)
        elif name == "analyze_compute_utilization":
            compartment_id = arguments.get("compartment_id")
            threshold = arguments.get("threshold", 30)
            result = await analyze_compute_handler(compartment_id, threshold)
        elif name == "list_idle_resources":
            compartment_id = arguments.get("compartment_id")
            result = await list_idle_resources_handler(compartment_id)
        elif name == "forecast_costs":
            days_ahead = arguments.get("days_ahead", 30)
            budget = arguments.get("budget_amount")
            result = await forecast_costs_handler(days_ahead, budget)
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


async def get_oci_costs_handler(days: int = 30, group_by: str = "service") -> dict:
    """Get OCI costs."""
    try:
        # In production, use OCI UsageApi here
        logger.info("Using mock OCI cost data")
        return get_mock_oci_costs(days, group_by)
    except Exception as e:
        logger.warning(f"OCI API failed, using mock data: {e}")
        return get_mock_oci_costs(days, group_by)


async def analyze_compute_handler(compartment_id: Optional[str] = None, threshold: int = 30) -> dict:
    """Analyze compute utilization."""
    try:
        logger.info("Using mock compute utilization data")
        return get_mock_compute_utilization(threshold)
    except Exception as e:
        logger.warning(f"OCI API failed, using mock data: {e}")
        return get_mock_compute_utilization(threshold)


async def list_idle_resources_handler(compartment_id: Optional[str] = None) -> dict:
    """List idle resources."""
    try:
        logger.info("Using mock idle resources data")
        return get_mock_idle_resources()
    except Exception as e:
        logger.warning(f"OCI API failed, using mock data: {e}")
        return get_mock_idle_resources()


async def forecast_costs_handler(days_ahead: int = 30, budget: Optional[float] = None) -> dict:
    """Forecast costs."""
    try:
        logger.info("Using mock cost forecast")
        return get_mock_cost_forecast(days_ahead, budget)
    except Exception as e:
        logger.warning(f"OCI API failed, using mock data: {e}")
        return get_mock_cost_forecast(days_ahead, budget)


# ============================================================================
# Server Entry Point
# ============================================================================

async def main():
    """Run the Cost Optimization MCP Server."""
    logger.info("Starting ODAOS Cost Optimization MCP Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            mcp.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
