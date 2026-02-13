# Pydantic Models for Visualization API

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Any
from datetime import datetime


class VizRequest(BaseModel):
    """Request for visualization generation."""
    query: str = Field(..., description="Natural language query")
    chart_type: Optional[Literal[
        "auto", "pie", "bar", "line", "scatter", 
        "heatmap", "treemap", "area"
    ]] = "auto"
    filters: Optional[dict] = None
    session_id: Optional[str] = None


class ChartData(BaseModel):
    """Chart data structure for frontend rendering."""
    chart_type: str
    title: str
    data: List[dict]
    layout: Optional[dict] = None
    config: Optional[dict] = None


class SmartNarrative(BaseModel):
    """AI-generated narrative explaining the chart."""
    summary: str
    key_insights: List[str]
    anomalies: List[dict] = []
    recommendations: List[str] = []


class DrillDownOption(BaseModel):
    """Option for drilling down into data."""
    label: str
    query: str
    dimension: str
    value: Any


class VizResponse(BaseModel):
    """Response from visualization endpoint."""
    chart: ChartData
    narrative: SmartNarrative
    drill_down_options: List[DrillDownOption] = []
    cross_filter_enabled: bool = True
    export_formats: List[str] = ["png", "svg", "pdf", "csv"]


class ChartExportRequest(BaseModel):
    """Request to export chart in specific format."""
    chart_data: ChartData
    format: Literal["png", "svg", "pdf", "csv"] = "png"
    width: int = 1200
    height: int = 800
