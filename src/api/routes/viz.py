# Visualization API Routes

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Literal
import json

from src.api.models.viz import VizRequest, VizResponse, ChartData, SmartNarrative
from src.api.services.viz_service import VizService


router = APIRouter()
viz_service = VizService()


@router.post("/smart", response_model=VizResponse)
async def smart_visualization(request: VizRequest):
    """
    Generate a smart visualization with auto-selected chart type.
    
    Features:
    - Automatic chart type selection based on data structure
    - Smart narrative generation explaining the chart
    - Drill-down options for deeper exploration
    - Cross-filter compatibility
    """
    result = await viz_service.generate_smart_viz(
        query=request.query,
        preferred_type=request.chart_type,
        filters=request.filters
    )
    return result


@router.get("/{chart_type}")
async def get_chart(
    chart_type: Literal["pie", "bar", "line", "scatter", "heatmap", "area"],
    query: str = Query(..., description="Natural language query for data"),
    filters: Optional[str] = None
):
    """Generate a specific chart type from query."""
    filter_dict = json.loads(filters) if filters else None
    
    chart_data = await viz_service.generate_chart(
        chart_type=chart_type,
        query=query,
        filters=filter_dict
    )
    
    return chart_data


@router.post("/drill-down")
async def drill_down(
    parent_query: str,
    dimension: str,
    value: str,
    chart_type: Optional[str] = None
):
    """
    Drill down into a specific data point.
    
    Example: From regional revenue pie chart, drill into "EMEA" region
    to see country-level breakdown.
    """
    result = await viz_service.drill_down(
        parent_query=parent_query,
        dimension=dimension,
        value=value,
        chart_type=chart_type
    )
    return result


@router.post("/cross-filter")
async def cross_filter(
    source_chart_id: str,
    selected_values: list[str],
    target_chart_ids: list[str]
):
    """
    Apply cross-filtering from one chart to others.
    
    When user selects data in one chart, this updates
    all linked charts to show filtered data.
    """
    results = await viz_service.apply_cross_filter(
        source_id=source_chart_id,
        selected=selected_values,
        targets=target_chart_ids
    )
    return {"updated_charts": results}


@router.get("/narrative/{chart_id}")
async def get_narrative(chart_id: str):
    """
    Get or regenerate smart narrative for a chart.
    
    Returns AI-generated text explaining:
    - What the chart shows
    - Key insights
    - Detected anomalies
    - Recommended actions
    """
    narrative = await viz_service.generate_narrative(chart_id)
    return narrative


@router.get("/export")
async def export_chart(
    chart_data: str,  # JSON string of ChartData
    format: Literal["png", "svg", "pdf", "csv"] = "png",
    width: int = 1200,
    height: int = 800
):
    """Export chart in specified format."""
    data = json.loads(chart_data)
    
    # For now, return a placeholder - actual export handled by frontend
    return {
        "status": "ready",
        "format": format,
        "dimensions": {"width": width, "height": height},
        "message": "Use frontend Plotly.downloadImage() for actual export"
    }
