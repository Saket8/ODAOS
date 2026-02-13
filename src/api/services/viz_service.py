# Visualization Service - Smart Chart Generation
# Refactored to delegate to AnalyticsAgent for unified query handling

import sys
import os
from typing import Optional, Dict, Any, List
from uuid import uuid4

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from src.api.models.viz import VizResponse, ChartData, SmartNarrative, DrillDownOption


class VizService:
    """
    Service for generating smart visualizations.
    
    Delegates query understanding to AnalyticsAgent for consistent behavior
    across CLI and Web interfaces.
    """
    
    def __init__(self):
        self._chart_cache: Dict[str, ChartData] = {}
        self._analytics_agent = None
    
    async def _get_analytics_agent(self):
        """Get AnalyticsAgent instance for query understanding."""
        if self._analytics_agent is None:
            from src.agents.analytics.agent import AnalyticsAgent
            self._analytics_agent = AnalyticsAgent()
        return self._analytics_agent
    
    async def generate_smart_viz(
        self,
        query: str,
        preferred_type: str = "auto",
        filters: Optional[Dict] = None,
        session_id: Optional[str] = None
    ) -> VizResponse:
        """
        Generate a visualization by delegating to AnalyticsAgent.
        
        The AnalyticsAgent handles:
        1. Query understanding (what data to fetch)
        2. Chart type selection (respects user preference)
        3. Data fetching from DataService
        4. Narrative generation
        """
        # Get unified query handling from AnalyticsAgent
        agent = await self._get_analytics_agent()
        viz_data = await agent.get_viz_data(query, preferred_type, thread_id=session_id)
        
        # Convert to ChartData model
        chart_data = ChartData(
            chart_type=viz_data["chart_type"],
            title=viz_data["title"],
            data=viz_data["data"],
            layout=self._get_chart_layout(
                viz_data["chart_type"],
                x_label=viz_data.get("x_axis_label"),
                y_label=viz_data.get("y_axis_label")
            ),
            config={"responsive": True, "displayModeBar": True}
        )
        
        # Convert narrative
        narrative_dict = viz_data["narrative"]
        narrative = SmartNarrative(
            summary=narrative_dict.get("summary", ""),
            key_insights=narrative_dict.get("key_insights", []),
            anomalies=[],
            recommendations=narrative_dict.get("recommendations", [])
        )
        
        # Get drill-down options
        drill_options = self._get_drill_down_options(query, chart_data)
        
        # Cache for cross-filtering
        chart_id = str(uuid4())
        self._chart_cache[chart_id] = chart_data
        
        return VizResponse(
            chart=chart_data,
            narrative=narrative,
            drill_down_options=drill_options,
            cross_filter_enabled=True
        )
    
    async def generate_chart(
        self,
        chart_type: str,
        query: str,
        filters: Optional[Dict] = None
    ) -> ChartData:
        """Generate a specific chart type."""
        agent = await self._get_analytics_agent()
        viz_data = await agent.get_viz_data(query, chart_type)
        
        return ChartData(
            chart_type=viz_data["chart_type"],
            title=viz_data["title"],
            data=viz_data["data"],
            layout=self._get_chart_layout(
                viz_data["chart_type"],
                x_label=viz_data.get("x_axis_label"),
                y_label=viz_data.get("y_axis_label")
            ),
            config={"responsive": True, "displayModeBar": True}
        )
    
    async def drill_down(
        self,
        parent_query: str,
        dimension: str,
        value: str,
        chart_type: Optional[str] = None
    ) -> VizResponse:
        """Drill down into a data point for deeper analysis."""
        drill_query = f"{parent_query} filtered by {dimension} = '{value}'"
        return await self.generate_smart_viz(
            query=drill_query,
            preferred_type=chart_type or "auto"
        )
    
    async def apply_cross_filter(
        self,
        source_id: str,
        selected: List[str],
        targets: List[str]
    ) -> List[Dict[str, Any]]:
        """Apply cross-filtering to linked charts."""
        results = []
        for target_id in targets:
            if target_id in self._chart_cache:
                filtered = self._filter_chart_data(
                    self._chart_cache[target_id],
                    selected
                )
                results.append({
                    "chartId": target_id,
                    "chart": filtered
                })
        return results
    
    def _get_drill_down_options(
        self,
        query: str,
        chart: ChartData
    ) -> List[DrillDownOption]:
        """Get available drill-down options for a chart."""
        return [
            DrillDownOption(
                label="Drill by Region",
                query=f"{query} by region",
                dimension="region",
                value="*"
            ),
            DrillDownOption(
                label="Drill by Product",
                query=f"{query} by product",
                dimension="product",
                value="*"
            ),
            DrillDownOption(
                label="Drill by Time Period",
                query=f"{query} over time",
                dimension="period",
                value="*"
            )
        ]
    
    def _filter_chart_data(
        self,
        chart: ChartData,
        filter_values: List[str]
    ) -> ChartData:
        """Filter chart data based on selected values."""
        filtered_data = [
            d for d in chart.data
            if any(str(v) in str(d.values()) for v in filter_values)
        ]
        return ChartData(
            chart_type=chart.chart_type,
            title=chart.title,
            data=filtered_data or chart.data,
            layout=chart.layout,
            config=chart.config
        )
    
    def _get_chart_layout(self, chart_type: str, x_label: Optional[str] = None, y_label: Optional[str] = None) -> Dict:
        """Get Plotly layout configuration for chart type with proper labeling."""
        base_layout = {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "color": "#E2E8F0"},
            "margin": {"l": 80, "r": 40, "t": 60, "b": 80}
        }
        
        if chart_type == "pie":
            base_layout["showlegend"] = True
        elif chart_type in ["bar", "line"]:
            base_layout["xaxis"] = {
                "gridcolor": "rgba(255,255,255,0.1)",
                "title": {"text": x_label, "font": {"size": 14, "color": "#94A3B8"}} if x_label else {}
            }
            base_layout["yaxis"] = {
                "gridcolor": "rgba(255,255,255,0.1)",
                "title": {"text": y_label, "font": {"size": 14, "color": "#94A3B8"}} if y_label else {}
            }
        
        elif chart_type == "heatmap":
            base_layout["xaxis"] = {
                "title": {"text": x_label or "Dimension X", "font": {"size": 14, "color": "#94A3B8"}}
            }
            base_layout["yaxis"] = {
                "title": {"text": y_label or "Dimension Y", "font": {"size": 14, "color": "#94A3B8"}}
            }
        
        return base_layout


# Singleton instance
_viz_service_instance = None

def get_viz_service() -> VizService:
    """Get singleton VizService instance."""
    global _viz_service_instance
    if _viz_service_instance is None:
        _viz_service_instance = VizService()
    return _viz_service_instance
