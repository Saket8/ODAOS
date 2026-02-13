# Chat Service - Integrates with ODAOS Orchestrator

import sys
import os
from typing import AsyncGenerator, Optional, List, Dict, Any
from uuid import uuid4

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from src.orchestrator import ODAOSOrchestrator
from src.agents.analytics.agent import AnalyticsAgent
from src.api.services.viz_service import VizService


class ChatService:
    """Service layer for chat functionality, integrating with ODAOS core."""
    
    def __init__(self):
        self.orchestrator: Optional[ODAOSOrchestrator] = None
        self.analytics_agent: Optional[AnalyticsAgent] = None
        self.viz_service: VizService = VizService()  # For Plotly chart generation
        self._initialized = False
        self._mock_mode = False  # Use mock responses if agents fail to initialize
    
    async def initialize(self):
        """Initialize the underlying agents."""
        if self._initialized:
            return
        
        try:
            # Both ODAOSOrchestrator and AnalyticsAgent initialize in __init__
            # No async initialize() methods needed
            self.orchestrator = ODAOSOrchestrator()
            self.analytics_agent = AnalyticsAgent()
            
            self._initialized = True
            print("[ChatService] Initialized with real agents")
        except Exception as e:
            import traceback
            print(f"[ChatService] Agent initialization failed: {e}")
            traceback.print_exc()
            self._mock_mode = True
            self._initialized = True
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        include_viz: bool = True
    ) -> Dict[str, Any]:
        """Process a chat message through the orchestrator."""
        if not self._initialized:
            await self.initialize()
        
        # Detect if this is an analytics query
        is_analytics = self._is_analytics_query(message)
        
        if is_analytics:
            response = await self.analytics_agent.chat(message)
            chart_data = await self._extract_chart_data(response) if include_viz else None
        else:
            response = await self.orchestrator.chat(message)
            chart_data = None
        
        suggestions = await self.generate_suggestions(message, response)
        
        return {
            "content": response,
            "chart_data": chart_data,
            "suggestions": suggestions,
            "is_analytics": is_analytics
        }
    
    async def stream_response(
        self,
        message: str,
        session_id: str
    ) -> AsyncGenerator[str, None]:
        """Stream LLM response token by token."""
        if not self._initialized:
            await self.initialize()
        
        is_analytics = self._is_analytics_query(message)
        
        if is_analytics:
            # For visualization queries, get narrative from viz_service
            try:
                viz_response = await self.viz_service.generate_smart_viz(message)
                narrative = viz_response.narrative
                
                # Build the narrative text response
                text_parts = []
                
                # Add summary
                if narrative.summary:
                    text_parts.append(f"**Summary:** {narrative.summary}")
                
                # Add key insights
                if narrative.key_insights:
                    text_parts.append("\n\n**Key Insights:**")
                    for insight in narrative.key_insights:
                        text_parts.append(f"\n• {insight}")
                
                # Add recommendations
                if narrative.recommendations:
                    text_parts.append("\n\n**Recommendations:**")
                    for rec in narrative.recommendations:
                        text_parts.append(f"\n💡 {rec}")
                
                response = "".join(text_parts) if text_parts else "Here is the visualization for your request:"
                
            except Exception as e:
                print(f"[ChatService] Viz narrative failed: {e}")
                response = "Here is the visualization for your request:"
            
            # Stream word by word
            words = response.split(' ')
            for i, word in enumerate(words):
                if i < len(words) - 1:
                    yield word + ' '
                else:
                    yield word
        else:
            # For non-viz queries, stream the full response
            response = await self.orchestrator.chat(message)
            words = response.split(' ')
            for i, word in enumerate(words):
                if i < len(words) - 1:
                    yield word + ' '
                else:
                    yield word
    
    async def generate_chart_if_needed(
        self,
        message: str,
        response: str,
        session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate Plotly chart data if the query warrants visualization."""
        if not self._is_analytics_query(message):
            return None
        
        # Pass the original message (query) and session_id to generate chart
        return await self._extract_chart_data(message, session_id)
    
    async def generate_suggestions(
        self,
        message: str,
        response: str
    ) -> List[str]:
        """Generate follow-up question suggestions."""
        # Context-aware suggestions based on query type
        suggestions = []
        
        message_lower = message.lower()
        
        if "customer" in message_lower:
            suggestions = [
                "Show customer churn rate",
                "What's the average customer lifetime value?",
                "Which regions have the highest customer growth?"
            ]
        elif "revenue" in message_lower:
            suggestions = [
                "Compare revenue by product category",
                "Show monthly revenue trends",
                "Which services generate the most revenue?"
            ]
        elif "product" in message_lower:
            suggestions = [
                "Show product adoption trends",
                "Which products have the highest churn?",
                "Compare product revenue by region"
            ]
        elif "database" in message_lower or "performance" in message_lower:
            suggestions = [
                "Show tablespace usage",
                "Are there any blocking sessions?",
                "What are the top resource-consuming queries?"
            ]
        else:
            suggestions = [
                "Show me key performance metrics",
                "What should I focus on today?",
                "Are there any anomalies in the data?"
            ]
        
        return suggestions[:3]
    
    async def get_proactive_insights(self, message: str) -> List[Dict[str, Any]]:
        """Get proactive AI-generated insights based on context."""
        # This would analyze data and surface relevant insights
        # For MVP, return static insights
        return []
    
    async def get_quick_replies(
        self,
        context: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Get quick reply buttons for chat interface."""
        if category == "analytics":
            return [
                {"text": "📊 Revenue Overview", "query": "Show revenue summary"},
                {"text": "👥 Customer Insights", "query": "Show customer distribution"},
                {"text": "📈 Trends", "query": "Show monthly trends"},
                {"text": "⚠️ Anomalies", "query": "Show any anomalies"}
            ]
        elif category == "database":
            return [
                {"text": "🔍 Health Check", "query": "How is the database?"},
                {"text": "💾 Tablespaces", "query": "Show tablespace usage"},
                {"text": "🔒 Sessions", "query": "Show active sessions"},
                {"text": "⚡ Performance", "query": "Show performance metrics"}
            ]
        else:
            return [
                {"text": "🎯 Get Started", "query": "What can you help me with?"},
                {"text": "📊 Analytics", "query": "Show analytics dashboard"},
                {"text": "🔍 Database Status", "query": "How is the database?"},
                {"text": "❓ Help", "query": "What questions can I ask?"}
            ]
    
    def _is_analytics_query(self, message: str) -> bool:
        """Detect if a message is an analytics/visualization query."""
        analytics_keywords = [
            "show", "chart", "graph", "plot", "visualize", "distribution",
            "trend", "revenue", "customer", "product", "compare", "breakdown",
            "pie", "bar", "line", "heatmap", "scatter", "analysis"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in analytics_keywords)
    
    async def _extract_chart_data(self, query: str, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Generate Plotly chart data using viz_service."""
        try:
            viz_response = await self.viz_service.generate_smart_viz(query, session_id=session_id)
            chart = viz_response.chart
            
            # Convert to Plotly format for frontend SmartChart component
            return {
                "id": str(uuid4()),
                "type": chart.chart_type,
                "title": chart.title,
                "data": chart.data,
                "layout": chart.layout,
                "config": chart.config,
                "narrative": {
                    "summary": viz_response.narrative.summary,
                    "insights": viz_response.narrative.key_insights,
                    "recommendations": viz_response.narrative.recommendations
                },
                "drillDownOptions": [
                    {"label": opt.label, "query": opt.query}
                    for opt in viz_response.drill_down_options
                ]
            }
        except Exception as e:
            print(f"[ChatService] Chart generation failed: {e}")
            return None
